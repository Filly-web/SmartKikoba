import os, secrets, csv, io
from datetime import datetime, date, timedelta
from calendar import monthrange
from decimal import Decimal, ROUND_HALF_UP
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func, and_
from openpyxl import Workbook, load_workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
db = SQLAlchemy()
migrate = Migrate()
CUT_OFF = date(2026, 10, 31)
LOAN_SNAPSHOT_DATE = date(2026, 10, 30)
ROLES = ["Administrator", "Chairman", "Secretary", "Treasurer", "Accountant", "Member"]
CENT = Decimal("0.01")
def money(v):
    return Decimal(str(v or 0)).quantize(CENT, rounding=ROUND_HALF_UP)
def fmt(v):
    return f"{money(v):,.2f}"
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)
class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_no = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(160), nullable=False)
    phone = db.Column(db.String(40))
    email = db.Column(db.String(160))
    joined_on = db.Column(db.Date, default=CUT_OFF)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class ContributionPeriod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    period = db.Column(db.String(7), unique=True, nullable=False)
    financial_year = db.Column(db.String(20), default="2026/2027")
    deadline_day = db.Column(db.Integer, default=30)
    minimum_amount = db.Column(db.Numeric(14,2), default=100000)
    share_pct = db.Column(db.Numeric(5,2), default=50)
    social_pct = db.Column(db.Numeric(5,2), default=50)
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"))
    loan_id = db.Column(db.Integer, db.ForeignKey("loan.id"))
    period_id = db.Column(db.Integer, db.ForeignKey("contribution_period.id"))
    txn_type = db.Column(db.String(30), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Numeric(14,2), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False)
    entry_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    description = db.Column(db.String(500))
    status = db.Column(db.String(20), default="Posted")
    reversed_by = db.Column(db.Integer, db.ForeignKey("transaction.id"))
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    member = db.relationship("Member", foreign_keys=[member_id])
    period = db.relationship("ContributionPeriod")
    def active(self): return self.status == "Posted"
class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_no = db.Column(db.String(40), unique=True, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    principal = db.Column(db.Numeric(14,2), nullable=False)
    rate = db.Column(db.Numeric(7,3), nullable=False)
    interest_total = db.Column(db.Numeric(14,2), nullable=False)
    installments = db.Column(db.Integer, nullable=False)
    first_due = db.Column(db.Date, nullable=False)
    disbursement_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default="Active")
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    member = db.relationship("Member")
    schedules = db.relationship("LoanInstallment", cascade="all, delete-orphan", order_by="LoanInstallment.installment_no")
class LoanInstallment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    loan_id = db.Column(db.Integer, db.ForeignKey("loan.id"), nullable=False)
    installment_no = db.Column(db.Integer, nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    principal_due = db.Column(db.Numeric(14,2), nullable=False)
    interest_due = db.Column(db.Numeric(14,2), nullable=False)
    principal_paid = db.Column(db.Numeric(14,2), default=0)
    interest_paid = db.Column(db.Numeric(14,2), default=0)
class OpeningBatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_ref = db.Column(db.String(50), unique=True, nullable=False)
    opening_date = db.Column(db.Date, default=CUT_OFF)
    mpesa_opening = db.Column(db.Numeric(14,2), default=0)
    status = db.Column(db.String(20), default="Draft")
    prepared_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    approved_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("OpeningBalance", cascade="all, delete-orphan")
class OpeningBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey("opening_batch.id"), nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey("member.id"), nullable=False)
    share = db.Column(db.Numeric(14,2), default=0)
    social = db.Column(db.Numeric(14,2), default=0)
    penalty = db.Column(db.Numeric(14,2), default=0)
    loan_principal = db.Column(db.Numeric(14,2), default=0)
    loan_interest = db.Column(db.Numeric(14,2), default=0)
    adjustment = db.Column(db.Numeric(14,2), default=0)
    adjustment_description = db.Column(db.String(300))
    member = db.relationship("Member")
    __table_args__ = (db.UniqueConstraint("batch_id","member_id", name="uq_opening_member"),)
class MpesaReconciliation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recon_date = db.Column(db.Date, nullable=False)
    expected_balance = db.Column(db.Numeric(14,2), nullable=False)
    actual_balance = db.Column(db.Numeric(14,2), nullable=False)
    difference = db.Column(db.Numeric(14,2), nullable=False)
    explanation = db.Column(db.String(1000))
    status = db.Column(db.String(30), default="Unmatched")
    prepared_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class CashMovement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movement_date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    amount = db.Column(db.Numeric(14,2), nullable=False)
    direction = db.Column(db.String(10), nullable=False) # IN or OUT
    description = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default="Posted")
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class Setting(db.Model):
    key = db.Column(db.String(80), primary_key=True)
    value = db.Column(db.String(250), nullable=False)
def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None
def login_required(fn):
    @wraps(fn)
    def wrap(*a, **kw):
        if not current_user(): return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrap
def roles_required(*roles):
    def deco(fn):
        @wraps(fn)
        def wrap(*a, **kw):
            u=current_user()
            if not u: return redirect(url_for("login"))
            if u.role not in roles: abort(403)
            return fn(*a, **kw)
        return wrap
    return deco
def txn_query(as_at=None, member_id=None):
    q=Transaction.query.filter_by(status="Posted")
    if as_at: q=q.filter(Transaction.transaction_date <= as_at)
    if member_id: q=q.filter_by(member_id=member_id)
    return q
def opening_position(member_id=None):
    q=OpeningBalance.query.join(OpeningBatch).filter(OpeningBatch.status=="Approved")
    if member_id: q=q.filter(OpeningBalance.member_id==member_id)
    rows=q.all()
    return {k:sum((money(getattr(x,k)) for x in rows), Decimal("0")) for k in ["share","social","penalty","loan_principal","loan_interest","adjustment"]}
def totals(as_at=None, member_id=None):
    op=opening_position(member_id)
    data={k:op.get(k,Decimal("0")) for k in op}
    for t in txn_query(as_at,member_id).all():
        if t.category=="SHARE": data["share"] += money(t.amount)
        elif t.category=="SOCIAL": data["social"] += money(t.amount)
        elif t.category=="PENALTY": data["social"] += money(t.amount); data["penalty"] += money(t.amount)
        elif t.category=="LOAN_DISBURSEMENT":
            data["loan_principal"] += money(t.amount)
            linked_loan=db.session.get(Loan,t.loan_id) if t.loan_id else None
            if linked_loan: data["loan_interest"] += money(linked_loan.interest_total)
        elif t.category=="LOAN_PRINCIPAL": data["loan_principal"] -= money(t.amount)
        elif t.category=="LOAN_INTEREST": data["loan_interest"] -= money(t.amount)
    return data
def loan_outstanding(loan):
    p=money(loan.principal); i=money(loan.interest_total)
    for inst in loan.schedules:
        p -= money(inst.principal_paid); i -= money(inst.interest_paid)
    return max(p,Decimal("0")), max(i,Decimal("0"))
def add_months(d, months):
    month_index=d.month-1+months
    year=d.year+month_index//12
    month=month_index%12+1
    return date(year,month,min(d.day,monthrange(year,month)[1]))
def build_schedule(loan):
    principal=money(loan.principal)
    interest=money(loan.interest_total)
    base=(principal/Decimal(loan.installments)).quantize(CENT, rounding=ROUND_HALF_UP)
    allocated=Decimal("0")
    for n in range(1,loan.installments+1):
        pr=base if n<loan.installments else principal-allocated
        allocated += pr
        due=add_months(loan.first_due,n-1)
        db.session.add(LoanInstallment(loan_id=loan.id, installment_no=n, due_date=due,
            principal_due=pr, interest_due=interest if n==1 else 0))
def apply_repayment(loan, amount, txn_date, reference, actor):
    amount=money(amount)
    remaining=amount
    if amount <= 0: raise ValueError("Repayment must be greater than zero.")
    p_out,i_out=loan_outstanding(loan)
    if amount > p_out+i_out: raise ValueError("Repayment exceeds outstanding loan balance.")
    for inst in loan.schedules:
        oi=money(inst.interest_due)-money(inst.interest_paid)
        op=money(inst.principal_due)-money(inst.principal_paid)
        x=min(remaining,oi)
        if x:
            inst.interest_paid=money(inst.interest_paid)+x
            db.session.add(Transaction(reference=reference+"-I",member_id=loan.member_id,loan_id=loan.id,
                txn_type="Receipt",category="LOAN_INTEREST",amount=x,transaction_date=txn_date,
                description="Loan interest received",created_by=actor))
            remaining-=x
        x=min(remaining,op)
        if x:
            inst.principal_paid=money(inst.principal_paid)+x
            db.session.add(Transaction(reference=reference+"-P",member_id=loan.member_id,loan_id=loan.id,
                txn_type="Receipt",category="LOAN_PRINCIPAL",amount=x,transaction_date=txn_date,
                description="Loan principal repaid",created_by=actor))
            remaining-=x
        if remaining<=0: break
    return amount
def expected_mpesa(as_at):
    opening=sum((money(x.mpesa_opening) for x in OpeningBatch.query.filter_by(status="Approved").filter(OpeningBatch.opening_date<=as_at)),Decimal("0"))
    # Movement-based reconciliation, so principal repayments are cash receipts but not profit.
    value=opening
    for t in txn_query(as_at).all():
        if t.category in ["SHARE","SOCIAL","PENALTY","LOAN_INTEREST","LOAN_PRINCIPAL"]:
            value += money(t.amount)
        elif t.category=="LOAN_DISBURSEMENT":
            value -= money(t.amount)
    for m in CashMovement.query.filter_by(status="Posted").filter(CashMovement.movement_date<=as_at).all():
        value += money(m.amount) if m.direction=="IN" else -money(m.amount)
    return value
def create_app():
    app=Flask(__name__)
    app.config["SECRET_KEY"]=os.getenv("SECRET_KEY","dev-only-change-this-secret")
    dburl=os.getenv("DATABASE_URL","sqlite:///kikoba_dev.db")
    if dburl.startswith("postgres://"): dburl=dburl.replace("postgres://","postgresql+psycopg://",1)
    elif dburl.startswith("postgresql://") and "+psycopg" not in dburl: dburl=dburl.replace("postgresql://","postgresql+psycopg://",1)
    app.config["SQLALCHEMY_DATABASE_URI"]=dburl
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]={"pool_pre_ping":True}
    db.init_app(app); migrate.init_app(app,db)
    @app.context_processor
    def inject():
        return {"user":current_user(),"fmt":fmt,"today":date.today()}
    @app.route("/")
    def home():
        if not current_user(): return redirect(url_for("login"))
        u=current_user()
        mid=u.member_id if u.role=="Member" else None
        as_at=request.args.get("as_at")
        try: d=date.fromisoformat(as_at) if as_at else date.today()
        except ValueError: d=date.today()
        t=totals(d,mid)
        loans=Loan.query.filter_by(member_id=mid).all() if mid else Loan.query.all()
        principal=sum((loan_outstanding(l)[0] for l in loans),Decimal("0"))
        interest=sum((loan_outstanding(l)[1] for l in loans),Decimal("0"))
        interest_realised=sum((money(x.amount) for x in txn_query(d,mid).filter_by(category="LOAN_INTEREST").all()),Decimal("0"))
        cash=expected_mpesa(d) if u.role!="Member" else None
        members=Member.query.filter_by(active=True).count() if not mid else 1
        return render_template("dashboard.html",t=t,loans=loans,principal=principal,interest=interest,
            interest_realised=interest_realised,cash=cash,members=members,as_at=d)
    @app.route("/login",methods=["GET","POST"])
    def login():
        if request.method=="POST":
            u=User.query.filter_by(username=request.form.get("username","").strip(),active=True).first()
            if u and u.check_password(request.form.get("password","")):
                session.clear(); session["user_id"]=u.id
                return redirect(url_for("home"))
            flash("Invalid username or password.","danger")
        return render_template("login.html")
    @app.route("/logout")
    def logout(): session.clear(); return redirect(url_for("login"))
    @app.route("/members",methods=["GET","POST"])
    @roles_required("Administrator","Chairman","Secretary","Treasurer","Accountant")
    def members():
        if request.method=="POST":
            no=request.form.get("member_no","").strip(); name=request.form.get("full_name","").strip()
            if not no or not name:
                flash("Member number and full name are required.","danger")
            elif Member.query.filter_by(member_no=no).first():
                flash("That member number already exists.","danger")
            else:
                m=Member(member_no=no,full_name=name,phone=request.form.get("phone"),email=request.form.get("email"))
                db.session.add(m); db.session.flush()
                db.session.commit(); flash("Member created.","success")
            return redirect(url_for("members"))
        return render_template("members.html",members=Member.query.order_by(Member.member_no).all())
    @app.route("/members/template")
    @roles_required("Administrator")
    def member_template():
        wb=Workbook(); ws=wb.active; ws.title="Members"
        ws.append(["Member No","Full Name","Phone","Email","Joined On"])
        ws.append(["VK-001","Jane Doe","0712345678","jane@example.com",date.today().isoformat()])
        return excel_send(wb,"Visionaries_Member_Upload_Template.xlsx")
    @app.route("/members/upload",methods=["POST"])
    @roles_required("Administrator")
    def member_upload():
        f=request.files.get("file")
        if not f or not f.filename.lower().endswith(".xlsx"):
            flash("Upload an Excel .xlsx member file.","danger"); return redirect(url_for("members"))
        try:
            ws=load_workbook(f,read_only=True,data_only=True).active
            headers={str(c.value).strip().lower():i for i,c in enumerate(ws[1]) if c.value is not None}
            required=["member no","full name"]
            if any(x not in headers for x in required): raise ValueError("Template must contain Member No and Full Name columns.")
            added=0; skipped=[]
            for rownum,row in enumerate(ws.iter_rows(min_row=2,values_only=True),start=2):
                no=str(row[headers["member no"]] or "").strip(); name=str(row[headers["full name"]] or "").strip()
                if not no and not name: continue
                if not no or not name: skipped.append(f"Row {rownum}: missing member number or name"); continue
                if Member.query.filter_by(member_no=no).first(): skipped.append(f"Row {rownum}: duplicate member number {no}"); continue
                phone=str(row[headers["phone"]]).strip() if "phone" in headers and row[headers["phone"]] is not None else None
                email=str(row[headers["email"]]).strip() if "email" in headers and row[headers["email"]] is not None else None
                joined=CUT_OFF
                if "joined on" in headers and row[headers["joined on"]]:
                    v=row[headers["joined on"]]
                    joined=v.date() if isinstance(v,datetime) else (v if isinstance(v,date) else date.fromisoformat(str(v)[:10]))
                db.session.add(Member(member_no=no,full_name=name,phone=phone,email=email,joined_on=joined)); added+=1
            db.session.commit(); flash(f"Imported {added} member(s). Skipped: {len(skipped)}.","success" if added else "warning")
            for msg in skipped[:8]: flash(msg,"warning")
        except Exception as e:
            db.session.rollback(); flash(f"Member upload failed: {e}","danger")
        return redirect(url_for("members"))
    @app.route("/members/<int:member_id>/edit",methods=["POST"])
    @roles_required("Administrator")
    def edit_member(member_id):
        m=db.get_or_404(Member,member_id); old={"member_no":m.member_no,"full_name":m.full_name,"phone":m.phone,"email":m.email}
        no=request.form.get("member_no","").strip(); name=request.form.get("full_name","").strip()
        duplicate=Member.query.filter(Member.member_no==no,Member.id!=m.id).first()
        if not no or not name or duplicate: flash("Enter a name and unique member number.","danger")
        else:
            m.member_no=no; m.full_name=name; m.phone=request.form.get("phone"); m.email=request.form.get("email")
            db.session.commit(); flash("Member details updated.","success")
        return redirect(url_for("members"))
    @app.route("/members/<int:member_id>/status",methods=["POST"])
    @roles_required("Administrator")
    def member_status(member_id):
        m=db.get_or_404(Member,member_id); m.active=not m.active
        db.session.commit()
        flash("Member status updated.","success"); return redirect(url_for("members"))
    @app.route("/members/<int:member_id>/delete",methods=["POST"])
    @roles_required("Administrator")
    def delete_member(member_id):
        m=db.get_or_404(Member,member_id)
        has_tx=Transaction.query.filter_by(member_id=m.id).first()
        has_loan=Loan.query.filter_by(member_id=m.id).first()
        has_opening=OpeningBalance.query.filter_by(member_id=m.id).first()
        has_user=User.query.filter_by(member_id=m.id).first()
        if has_tx or has_loan or has_opening or has_user:
            flash("This member has financial records or a linked login. Deactivate the member instead; records are protected.","warning")
        else:
            db.session.delete(m); db.session.commit(); flash("Member deleted.","success")
        return redirect(url_for("members"))
    @app.route("/contributions",methods=["GET","POST"])
    @login_required
    def contributions():
        if request.method=="POST" and current_user().role=="Member": abort(403)
        if request.method=="POST":
            d=date.fromisoformat(request.form["transaction_date"])
            if d<date(2026,10,1): flash("Use the historical Excel upload for dates before October 2026.","danger"); return redirect(url_for("contributions"))
            amt=money(request.form["amount"])
            if amt<=0: flash("Amount must be positive.","danger"); return redirect(url_for("contributions"))
            cat=request.form["category"]
            if cat not in ["SHARE","SOCIAL","PENALTY"]: abort(400)
            period=request.form.get("period") or d.strftime("%Y-%m")
            cp=ContributionPeriod.query.filter_by(period=period).first()
            if not cp: cp=ContributionPeriod(period=period); db.session.add(cp); db.session.flush()
            ref="CON-"+secrets.token_hex(7).upper()
            tx=Transaction(reference=ref,member_id=int(request.form["member_id"]),period_id=cp.id,txn_type="Receipt",
                category=cat,amount=amt,transaction_date=d,description=request.form.get("description"),created_by=current_user().id)
            db.session.add(tx)
            db.session.commit(); flash("Contribution posted.","success"); return redirect(url_for("contributions"))
        q=Transaction.query.filter(Transaction.category.in_(["SHARE","SOCIAL","PENALTY"])).order_by(Transaction.transaction_date.desc())
        if current_user().role=="Member": q=q.filter_by(member_id=current_user().member_id)
        return render_template("contributions.html",members=Member.query.filter_by(active=True).all(),rows=q.limit(200).all())
    @app.route("/loans",methods=["GET","POST"])
    @login_required
    def loans():
        if request.method=="POST" and current_user().role=="Member": abort(403)
        if request.method=="POST":
            d=date.fromisoformat(request.form["disbursement_date"]); first=date.fromisoformat(request.form["first_due"])
            if d<date(2026,11,1): flash("For opening loans dated on or before 30 October 2026, use the Outstanding Loans upload. New loans can be posted from 1 November 2026 onward.","danger"); return redirect(url_for("loans"))
            p=money(request.form["principal"]); rate=money(request.form["rate"]); n=int(request.form["installments"])
            if p<=0 or n<1 or n>60 or rate<0: flash("Check principal, rate and installment count.","danger"); return redirect(url_for("loans"))
            interest=money(p*rate/Decimal("100"))
            loan=Loan(loan_no="LN-"+secrets.token_hex(5).upper(),member_id=int(request.form["member_id"]),principal=p,
                rate=rate,interest_total=interest,installments=n,first_due=first,disbursement_date=d,created_by=current_user().id)
            db.session.add(loan); db.session.flush(); build_schedule(loan)
            db.session.add(Transaction(reference=loan.loan_no+"-OUT",member_id=loan.member_id,loan_id=loan.id,txn_type="Disbursement",
                category="LOAN_DISBURSEMENT",amount=p,transaction_date=d,description="Loan disbursement",created_by=current_user().id))
            db.session.commit(); flash("Loan and repayment schedule created.","success"); return redirect(url_for("loans"))
        ls=Loan.query.order_by(Loan.disbursement_date.desc()).all()
        if current_user().role=="Member": ls=[x for x in ls if x.member_id==current_user().member_id]
        return render_template("loans.html",members=Member.query.filter_by(active=True).all(),loans=ls)
    @app.route("/loans/<int:loan_id>/receipt.pdf")
    @login_required
    def loan_receipt(loan_id):
        loan=db.get_or_404(Loan,loan_id); u=current_user()
        if u.role=="Member" and u.member_id!=loan.member_id: abort(403)
        if u.role not in ["Administrator","Chairman","Secretary","Treasurer","Accountant","Member"]: abort(403)
        buff=io.BytesIO(); pdf=canvas.Canvas(buff,pagesize=A4); width,height=A4; y=height-55
        pdf.setTitle(f"Loan Receipt {loan.loan_no}")
        pdf.setFont("Helvetica-Bold",17); pdf.drawString(48,y,"VISIONARIES SMART KIKOBA"); y-=28
        pdf.setFont("Helvetica-Bold",13); pdf.drawString(48,y,"LOAN RECEIPT & REPAYMENT PLAN"); y-=30
        pdf.setFont("Helvetica",10)
        details=[("Loan reference",loan.loan_no),("Member",f"{loan.member.member_no} - {loan.member.full_name}"),("Disbursement date",loan.disbursement_date.strftime("%d %b %Y")),("Principal (TZS)",fmt(loan.principal)),("Flat interest rate",f"{loan.rate}%"),("Total interest (TZS)",fmt(loan.interest_total)),("Total repayable (TZS)",fmt(money(loan.principal)+money(loan.interest_total))),("Repayment instalments",str(loan.installments)),("First due date",loan.first_due.strftime("%d %b %Y"))]
        for label,value in details:
            pdf.setFont("Helvetica-Bold",10); pdf.drawString(48,y,label+":")
            pdf.setFont("Helvetica",10); pdf.drawString(205,y,str(value)); y-=19
        y-=10; pdf.setFont("Helvetica-Bold",10)
        for x,label in [(48,"No."),(90,"Due date"),(190,"Principal (TZS)"),(310,"Interest (TZS)"),(430,"Total (TZS)")]: pdf.drawString(x,y,label)
        y-=8; pdf.line(48,y,545,y); y-=17; pdf.setFont("Helvetica",9)
        for inst in loan.schedules:
            if y<65: pdf.showPage(); y=height-55; pdf.setFont("Helvetica",9)
            total=money(inst.principal_due)+money(inst.interest_due)
            for x,value in [(48,str(inst.installment_no)),(90,inst.due_date.strftime("%d %b %Y")),(190,fmt(inst.principal_due)),(310,fmt(inst.interest_due)),(430,fmt(total))]: pdf.drawString(x,y,value)
            y-=17
        p_out,i_out=loan_outstanding(loan); y-=15; pdf.setFont("Helvetica-Bold",10)
        pdf.drawString(48,y,f"Outstanding principal: TZS {fmt(p_out)}"); y-=18
        pdf.drawString(48,y,f"Outstanding interest: TZS {fmt(i_out)}"); y-=28
        pdf.setFont("Helvetica-Oblique",8); pdf.drawString(48,y,"This receipt is system-generated. Retain it as evidence of the loan and agreed repayment schedule.")
        pdf.save(); buff.seek(0)
        return send_file(buff,mimetype="application/pdf",as_attachment=True,download_name=f"{loan.loan_no}_Loan_Receipt.pdf")
    @app.route("/loans/<int:loan_id>/repay",methods=["POST"])
    @roles_required("Administrator","Chairman","Secretary","Treasurer","Accountant")
    def repay(loan_id):
        loan=db.get_or_404(Loan,loan_id)
        try:
            d=date.fromisoformat(request.form["transaction_date"])
            if d<date(2026,11,1): raise ValueError("For repayments dated on or before 30 October 2026, include the cumulative amount in the Outstanding Loans opening upload. New repayments can be posted from 1 November 2026 onward.")
            ref="REP-"+secrets.token_hex(6).upper()
            apply_repayment(loan,request.form["amount"],d,ref,current_user().id)
            p_out,i_out=loan_outstanding(loan)
            loan.status="Closed" if p_out+i_out==0 else "Active"
            db.session.commit(); flash("Repayment allocated to earliest outstanding instalment: interest first, then principal.","success")
        except Exception as e:
            db.session.rollback(); flash(str(e),"danger")
        return redirect(url_for("loans"))
    @app.route("/opening",methods=["GET","POST"])
    @roles_required("Administrator","Chairman","Accountant")
    def opening():
        if request.method=="POST":
            action=request.form.get("action")
            if action=="manual":
                opening_date=date.fromisoformat(request.form.get("opening_date") or "2026-10-31")
                if opening_date != date(2026,10,31):
                    flash("This version uses 31 October 2026 as the opening balance date.","danger")
                    return redirect(url_for("opening"))
                batch=OpeningBatch(batch_ref="OPEN-"+secrets.token_hex(5).upper(),opening_date=opening_date,mpesa_opening=money(request.form.get("mpesa_opening",0)),prepared_by=current_user().id)
                db.session.add(batch); db.session.flush()
                for m in Member.query.filter_by(active=True).all():
                    vals={k:money(request.form.get(f"{k}_{m.id}",0)) for k in ["share","social","penalty","loan_principal","loan_interest","adjustment"]}
                    if vals["loan_principal"] or vals["loan_interest"]:
                        flash("Do not enter aggregate loan balances in the 31 October opening sheet. Upload each loan separately so its instalments can be tracked individually.","danger")
                        db.session.rollback(); return redirect(url_for("opening"))
                    if any(vals.values()):
                        db.session.add(OpeningBalance(batch_id=batch.id,member_id=m.id,**vals,adjustment_description=request.form.get(f"desc_{m.id}")))
                db.session.commit(); flash("Opening balance batch saved as Draft. Chairman approval is required.","success")
            elif action=="approve":
                b=db.get_or_404(OpeningBatch,int(request.form["batch_id"]))
                if b.status!="Draft": flash("Only draft opening batches can be approved.","warning")
                else:
                    b.status="Approved"; b.approved_by=current_user().id
                    db.session.commit(); flash("Opening balances approved and locked.","success")
            return redirect(url_for("opening"))
        return render_template("opening.html",members=Member.query.filter_by(active=True).all(),
            batches=OpeningBatch.query.order_by(OpeningBatch.created_at.desc()).all())
    @app.route("/opening/template")
    @roles_required("Administrator","Chairman","Accountant")
    def opening_template():
        wb=Workbook(); ws=wb.active; ws.title="Opening Balances"
        ws.append(["Member No","Member Name","SHARE","SOCIAL","Unpaid Penalty","Loan Principal","Loan Interest","Other Adjustment","Adjustment Description"])
        for m in Member.query.filter_by(active=True).all(): ws.append([m.member_no,m.full_name,0,0,0,0,0,0,""])
        return excel_send(wb,"Visionaries_Opening_Balances_Template.xlsx")
    @app.route("/opening/upload",methods=["POST"])
    @roles_required("Administrator","Accountant")
    def opening_upload():
        f=request.files.get("file")
        if not f: flash("Select an Excel file.","danger"); return redirect(url_for("opening"))
        try:
            wb=load_workbook(f,data_only=True); ws=wb.active
            heads=[str(c.value or "").strip() for c in ws[1]]
            idx={h:i for i,h in enumerate(heads)}
            required=["Member No","SHARE","SOCIAL","Unpaid Penalty","Loan Principal","Loan Interest","Other Adjustment"]
            if any(x not in idx for x in required): raise ValueError("Template columns do not match.")
            opening_date=date.fromisoformat(request.form.get("opening_date") or "2026-10-31")
            if opening_date != date(2026,10,31): raise ValueError("This release is configured for the opening balance date 31 October 2026.")
            batch=OpeningBatch(batch_ref="OPEN-"+secrets.token_hex(5).upper(),opening_date=opening_date,prepared_by=current_user().id)
            db.session.add(batch); db.session.flush()
            for row in ws.iter_rows(min_row=2,values_only=True):
                if not row[idx["Member No"]]: continue
                m=Member.query.filter_by(member_no=str(row[idx["Member No"]]).strip()).first()
                if not m: raise ValueError(f"Unknown member: {row[idx['Member No']]}")
                vals={"share":money(row[idx["SHARE"]]),"social":money(row[idx["SOCIAL"]]),"penalty":money(row[idx["Unpaid Penalty"]]),
                    "loan_principal":money(row[idx["Loan Principal"]]),"loan_interest":money(row[idx["Loan Interest"]]),
                    "adjustment":money(row[idx["Other Adjustment"]])}
                if vals["loan_principal"] or vals["loan_interest"]:
                    raise ValueError("Set Loan Principal and Loan Interest to zero here. Upload each loan separately using Outstanding Loans as at 30 October 2026.")
                db.session.add(OpeningBalance(batch_id=batch.id,member_id=m.id,**vals,
                    adjustment_description=str(row[idx["Adjustment Description"]] or "") if "Adjustment Description" in idx else ""))
            db.session.commit()
            flash("Opening balance upload saved as Draft. Review and obtain Chairman approval.","success")
        except Exception as e:
            db.session.rollback(); flash(f"Upload rejected: {e}","danger")
        return redirect(url_for("opening"))
    @app.route("/loans/opening-template")
    @roles_required("Administrator","Chairman","Accountant")
    def loan_opening_template():
        wb=Workbook(); ws=wb.active; ws.title="Outstanding Loans"
        ws.append(["Loan No","Member No","Original Loan Date","Original Loan Amount","Flat Interest Rate %","Total Instalments","Instalments Paid as at 30-Oct-2026","Amount Paid as at 30-Oct-2026","First Instalment Due Date"])
        ws.append(["OPEN-LN-001","REPLACE-WITH-MEMBER-NO","2026-05-15",500000,10,6,2,216666.66,"2026-06-15"])
        ws.append([])
        ws.append(["IMPORTANT: enter one row per loan. Amount Paid is the cumulative amount actually received up to 30 October 2026. Instalments Paid means the number of complete instalments settled; any additional partial payment is included in Amount Paid."])
        return excel_send(wb,"Visionaries_Outstanding_Loans_as_at_30_October_2026.xlsx")

    @app.route("/loans/opening-upload",methods=["POST"])
    @roles_required("Administrator","Accountant")
    def loan_opening_upload():
        f=request.files.get("file")
        if not f:
            flash("Select the Outstanding Loans Excel workbook.","danger"); return redirect(url_for("opening"))
        try:
            wb=load_workbook(f,data_only=True)
            if "Outstanding Loans" not in wb.sheetnames: raise ValueError("Workbook must contain the Outstanding Loans sheet. Download the supplied template.")
            ws=wb["Outstanding Loans"]
            headers=[str(c.value or "").strip() for c in ws[1]]; ix={h:i for i,h in enumerate(headers)}
            required=["Loan No","Member No","Original Loan Date","Original Loan Amount","Flat Interest Rate %","Total Instalments","Instalments Paid as at 30-Oct-2026","Amount Paid as at 30-Oct-2026","First Instalment Due Date"]
            missing=[h for h in required if h not in ix]
            if missing: raise ValueError("Missing columns: "+", ".join(missing))
            actor=current_user().id; count=0; seen=set()
            def xdate(value, label):
                if isinstance(value, datetime): return value.date()
                if isinstance(value, date): return value
                try: return date.fromisoformat(str(value)[:10])
                except Exception: raise ValueError(f"Invalid {label}: {value}")
            for row in ws.iter_rows(min_row=2,values_only=True):
                if not row or not row[ix["Loan No"]]: continue
                no=str(row[ix["Loan No"]]).strip()
                if no in seen or Loan.query.filter_by(loan_no=no).first(): raise ValueError(f"Duplicate loan number: {no}")
                seen.add(no)
                member_no=str(row[ix["Member No"]] or "").strip(); member=Member.query.filter_by(member_no=member_no).first()
                if not member: raise ValueError(f"Unknown member number for loan {no}: {member_no}")
                disb=xdate(row[ix["Original Loan Date"]],"original loan date")
                first=xdate(row[ix["First Instalment Due Date"]],"first instalment due date")
                if disb>LOAN_SNAPSHOT_DATE: raise ValueError(f"{no}: original loan date must be on or before 30 October 2026.")
                if first<=disb: raise ValueError(f"{no}: first instalment due date must be after the original loan date.")
                principal=money(row[ix["Original Loan Amount"]]); rate=money(row[ix["Flat Interest Rate %"]])
                n=int(row[ix["Total Instalments"]] or 0); paid_n=int(row[ix["Instalments Paid as at 30-Oct-2026"]] or 0)
                paid=money(row[ix["Amount Paid as at 30-Oct-2026"]])
                if principal<=0 or rate<0 or n<1 or n>60 or paid_n<0 or paid_n>n: raise ValueError(f"{no}: invalid loan amount, rate or instalment count.")
                interest=money(principal*rate/Decimal("100")); total=principal+interest
                if paid<0 or paid>total: raise ValueError(f"{no}: amount paid must be between zero and total repayable ({fmt(total)}).")
                if Transaction.query.filter_by(reference=no+"-OUT").first(): raise ValueError(f"Disbursement reference already exists for {no}.")
                if paid>0 and Transaction.query.filter(Transaction.reference.in_([no+"-OPENPAY-I",no+"-OPENPAY-P"])).first(): raise ValueError(f"Opening repayment reference already exists for {no}.")
                loan=Loan(loan_no=no,member_id=member.id,principal=principal,rate=rate,interest_total=interest,installments=n,first_due=first,disbursement_date=disb,created_by=actor)
                db.session.add(loan); db.session.flush(); build_schedule(loan)
                schedule=list(loan.schedules)
                full_paid=sum((money(x.principal_due)+money(x.interest_due) for x in schedule[:paid_n]),Decimal("0"))
                next_boundary=sum((money(x.principal_due)+money(x.interest_due) for x in schedule[:min(paid_n+1,n)]),Decimal("0"))
                if paid+Decimal("0.01")<full_paid:
                    raise ValueError(f"{no}: amount paid ({fmt(paid)}) is insufficient for {paid_n} fully paid instalments ({fmt(full_paid)} required).")
                if paid_n<n and paid>=next_boundary+Decimal("0.01"):
                    raise ValueError(f"{no}: amount paid is enough for more instalments than the {paid_n} reported as paid. Increase the paid-instalment count.")
                db.session.add(Transaction(reference=no+"-OUT",member_id=member.id,loan_id=loan.id,txn_type="Disbursement",category="LOAN_DISBURSEMENT",amount=principal,transaction_date=disb,description="Opening loan register: original disbursement",created_by=actor))
                if paid>0: apply_repayment(loan,paid,LOAN_SNAPSHOT_DATE,no+"-OPENPAY",actor)
                p_out,i_out=loan_outstanding(loan)
                loan.status="Closed" if p_out+i_out==0 else "Active"
                count+=1
            if count==0: raise ValueError("No loan rows were found in the worksheet.")
            db.session.commit()
            flash(f"Outstanding loan register loaded as at 30 October 2026: {count} loans. Instalments, amounts paid and remaining schedules are now tracked individually.","success")
        except Exception as e:
            db.session.rollback(); flash(f"Loan opening upload rejected; no loans were posted. {e}","danger")
        return redirect(url_for("opening"))

    @app.route("/historical/template")
    @roles_required("Administrator","Chairman","Accountant")
    def historical_template():
        wb=Workbook(); ws=wb.active; ws.title="Contributions"
        ws.append(["Reference","Transaction Date","Member No","Category","Amount","Description"])
        ws.append(["HIST-CON-001","2026-11-05","REPLACE-WITH-MEMBER-NO","SHARE",100000,"November contribution"])
        loans=wb.create_sheet("Loans")
        loans.append(["Loan No","Member No","Disbursement Date","Principal","Flat Interest Rate %","Installments","First Due Date"])
        loans.append(["HIST-LN-001","REPLACE-WITH-MEMBER-NO","2026-11-10",500000,10,5,"2026-12-10"])
        reps=wb.create_sheet("Repayments")
        reps.append(["Reference","Loan No","Repayment Date","Amount","Description"])
        reps.append(["HIST-REP-001","HIST-LN-001","2026-12-10",110000,"First instalment"])
        return excel_send(wb,"Visionaries_Historical_Transactions_Template.xlsx")
    @app.route("/historical/upload",methods=["GET","POST"])
    @roles_required("Administrator","Chairman","Accountant")
    def historical_upload():
        if request.method=="GET": return redirect(url_for("opening"))
        f=request.files.get("file")
        if not f: flash("Select the historical Excel workbook.","danger"); return redirect(url_for("opening"))
        try:
            wb=load_workbook(f,data_only=True)
            if not all(x in wb.sheetnames for x in ["Contributions","Loans","Repayments"]):
                raise ValueError("Workbook must contain Contributions, Loans and Repayments sheets. Download the supplied template.")
            opening=OpeningBatch.query.filter_by(status="Approved").order_by(OpeningBatch.opening_date.desc()).first()
            if not opening: raise ValueError("Approve the 31 October 2026 opening balance before uploading historical transactions.")
            lower=opening.opening_date + timedelta(days=1); upper=date.today(); actor=current_user().id
            counts={"contributions":0,"loans":0,"repayments":0}
            seen_refs=set(); seen_loans=set()
            # Validate headers before posting anything; all changes are one database transaction.
            def rows_for(sheet, required):
                sh=wb[sheet]; headers=[str(c.value or "").strip() for c in sh[1]]; ix={h:i for i,h in enumerate(headers)}
                missing=[h for h in required if h not in ix]
                if missing: raise ValueError(f"{sheet}: missing columns: {', '.join(missing)}")
                return sh,ix
            sh,ix=rows_for("Contributions",["Reference","Transaction Date","Member No","Category","Amount"])
            for row in sh.iter_rows(min_row=2,values_only=True):
                if not row or not row[ix["Reference"]]: continue
                ref=str(row[ix["Reference"]]).strip(); d=date.fromisoformat(str(row[ix["Transaction Date"]])[:10])
                if not lower<=d<=upper: raise ValueError(f"{ref}: date must be between the day after the approved opening date and today.")
                if ref in seen_refs or Transaction.query.filter_by(reference=ref).first(): raise ValueError(f"Duplicate transaction reference: {ref}")
                seen_refs.add(ref)
                m=Member.query.filter_by(member_no=str(row[ix["Member No"]]).strip()).first()
                if not m: raise ValueError(f"Unknown member number in {ref}: {row[ix['Member No']]}")
                cat=str(row[ix["Category"]]).strip().upper(); amt=money(row[ix["Amount"]])
                if cat not in ["SHARE","SOCIAL","PENALTY"] or amt<=0: raise ValueError(f"{ref}: invalid category or amount.")
                period=d.strftime("%Y-%m"); cp=ContributionPeriod.query.filter_by(period=period).first()
                if not cp: cp=ContributionPeriod(period=period); db.session.add(cp); db.session.flush()
                db.session.add(Transaction(reference=ref,member_id=m.id,period_id=cp.id,txn_type="Receipt",category=cat,amount=amt,transaction_date=d,description=str(row[ix["Description"]] or "Historical contribution") if "Description" in ix else "Historical contribution",created_by=actor))
                counts["contributions"]+=1
            sh,ix=rows_for("Loans",["Loan No","Member No","Disbursement Date","Principal","Flat Interest Rate %","Installments","First Due Date"])
            for row in sh.iter_rows(min_row=2,values_only=True):
                if not row or not row[ix["Loan No"]]: continue
                no=str(row[ix["Loan No"]]).strip(); d=date.fromisoformat(str(row[ix["Disbursement Date"]])[:10]); first=date.fromisoformat(str(row[ix["First Due Date"]])[:10])
                if not lower<=d<=upper: raise ValueError(f"{no}: disbursement date must be between the day after the approved opening date and today.")
                if Loan.query.filter_by(loan_no=no).first(): raise ValueError(f"Duplicate loan number: {no}")
                if Transaction.query.filter_by(reference=no+"-OUT").first(): raise ValueError(f"Loan disbursement reference already exists: {no}-OUT")
                m=Member.query.filter_by(member_no=str(row[ix["Member No"]]).strip()).first()
                if not m: raise ValueError(f"Unknown member for loan {no}.")
                principal=money(row[ix["Principal"]]); rate=money(row[ix["Flat Interest Rate %"]]); n=int(row[ix["Installments"]])
                if principal<=0 or rate<0 or n<1 or n>60: raise ValueError(f"{no}: invalid principal, interest rate or installment count.")
                loan=Loan(loan_no=no,member_id=m.id,principal=principal,rate=rate,interest_total=money(principal*rate/Decimal('100')),installments=n,first_due=first,disbursement_date=d,created_by=actor)
                db.session.add(loan); db.session.flush(); build_schedule(loan)
                db.session.add(Transaction(reference=no+"-OUT",member_id=m.id,loan_id=loan.id,txn_type="Disbursement",category="LOAN_DISBURSEMENT",amount=principal,transaction_date=d,description="Historical loan disbursement",created_by=actor))
                counts["loans"]+=1
            sh,ix=rows_for("Repayments",["Reference","Loan No","Repayment Date","Amount"])
            for row in sh.iter_rows(min_row=2,values_only=True):
                if not row or not row[ix["Reference"]]: continue
                ref=str(row[ix["Reference"]]).strip(); d=date.fromisoformat(str(row[ix["Repayment Date"]])[:10]); no=str(row[ix["Loan No"]]).strip()
                if not lower<=d<=upper: raise ValueError(f"{ref}: repayment date must be between the day after the approved opening date and today.")
                if ref in seen_refs or Transaction.query.filter_by(reference=ref).first() or Transaction.query.filter(Transaction.reference.in_([ref+"-I",ref+"-P"])).first(): raise ValueError(f"Duplicate repayment reference: {ref}")
                seen_refs.add(ref)
                loan=Loan.query.filter_by(loan_no=no).first()
                if not loan: raise ValueError(f"Unknown loan number for repayment {ref}: {no}. Add the loan on the Loans sheet first.")
                apply_repayment(loan,money(row[ix["Amount"]]),d,ref,actor); counts["repayments"]+=1
            db.session.commit()
            flash(f"Historical upload completed: {counts['contributions']} contributions, {counts['loans']} loans and {counts['repayments']} repayments.","success")
        except Exception as e:
            db.session.rollback(); flash(f"Upload rejected; no rows were posted. {e}","danger")
        return redirect(url_for("opening"))

    @app.route("/reconciliation",methods=["GET","POST"])
    @roles_required("Administrator","Chairman","Accountant")
    def reconciliation():
        if request.method=="POST":
            d=date.fromisoformat(request.form["recon_date"]); exp=money(expected_mpesa(d)); actual=money(request.form["actual_balance"])
            diff=actual-exp
            r=MpesaReconciliation(recon_date=d,expected_balance=exp,actual_balance=actual,difference=diff,
                explanation=request.form.get("explanation"),status="Matched" if diff==0 else "Unmatched",prepared_by=current_user().id)
            db.session.add(r); db.session.flush()
            db.session.commit(); flash("Reconciliation saved. Differences are not automatically adjusted.","success")
            return redirect(url_for("reconciliation"))
        return render_template("reconciliation.html",rows=MpesaReconciliation.query.order_by(MpesaReconciliation.recon_date.desc()).all(),
            expected=expected_mpesa(date.today()))
    @app.route("/reconciliation/<int:rid>/approve",methods=["POST"])
    @roles_required("Administrator","Chairman")
    def recon_approve(rid):
        r=db.get_or_404(MpesaReconciliation,rid)
        r.status="Approved"; r.reviewed_by=current_user().id
        db.session.commit(); flash("Reconciliation reviewed. Any difference remains recorded.","success")
        return redirect(url_for("reconciliation"))
    @app.route("/cash-movements",methods=["GET","POST"])
    @roles_required("Administrator","Chairman","Accountant")
    def cash_movements():
        if request.method=="POST":
            m=CashMovement(movement_date=date.fromisoformat(request.form["movement_date"]),category=request.form["category"],
                amount=money(request.form["amount"]),direction=request.form["direction"],description=request.form["description"],
                created_by=current_user().id)
            if m.amount<=0: flash("Amount must be positive.","danger")
            else:
                db.session.add(m); db.session.commit()
                flash("Cash movement recorded.","success")
            return redirect(url_for("cash_movements"))
        return render_template("cash_movements.html",rows=CashMovement.query.order_by(CashMovement.movement_date.desc()).all())
    @app.route("/reports")
    @login_required
    def reports():
        u=current_user(); mid=u.member_id if u.role=="Member" else request.args.get("member_id",type=int)
        try: d=date.fromisoformat(request.args.get("as_at","")) if request.args.get("as_at") else date.today()
        except ValueError: d=date.today()
        t=totals(d,mid)
        loans=Loan.query.filter_by(member_id=mid).all() if mid else Loan.query.all()
        if u.role=="Member": loans=[l for l in loans if l.member_id==u.member_id]
        rows=txn_query(d,mid).order_by(Transaction.transaction_date.desc()).all()
        return render_template("reports.html",t=t,loans=loans,rows=rows,members=Member.query.all(),selected=mid,as_at=d)
    @app.route("/reports/export.xlsx")
    @login_required
    def export_report():
        u=current_user(); mid=u.member_id if u.role=="Member" else request.args.get("member_id",type=int)
        try: d=date.fromisoformat(request.args.get("as_at","")) if request.args.get("as_at") else date.today()
        except ValueError: d=date.today()
        wb=Workbook(); ws=wb.active; ws.title="Financial Position"
        t=totals(d,mid)
        ws.append(["VISIONARIES SMART KIKOBA","As at",d.isoformat()])
        ws.append(["Category","Amount (TZS)"])
        for k,v in t.items(): ws.append([k.replace("_"," ").title(),float(v)])
        tx=wb.create_sheet("Transactions"); tx.append(["Reference","Transaction Date","Entry Date/Time","Member","Category","Amount","Status","Description"])
        q=txn_query(d,mid).order_by(Transaction.transaction_date)
        for x in q.all(): tx.append([x.reference,x.transaction_date.isoformat(),x.entry_date.isoformat(),x.member.full_name if x.member else "",x.category,float(x.amount),x.status,x.description])
        return excel_send(wb,f"Kikoba_Report_{d.isoformat()}.xlsx")
    @app.route("/users",methods=["GET","POST"])
    @roles_required("Administrator")
    def users():
        if request.method=="POST":
            username=request.form["username"].strip()
            if User.query.filter_by(username=username).first(): flash("Username already exists.","danger")
            else:
                u=User(username=username,full_name=request.form["full_name"],role=request.form["role"],
                    member_id=request.form.get("member_id",type=int) or None)
                u.set_password(request.form["password"]); db.session.add(u)
                db.session.commit(); flash("User created.","success")
            return redirect(url_for("users"))
        return render_template("users.html",users=User.query.all(),members=Member.query.all(),roles=ROLES)
    @app.route("/settings",methods=["GET","POST"])
    @roles_required("Administrator")
    def settings():
        if request.method=="POST":
            for key in ["minimum_contribution","share_pct","social_pct","penalty_method","penalty_rate","penalty_fixed","grace_days","deadline_day"]:
                s=db.session.get(Setting,key)
                if not s: s=Setting(key=key,value=request.form.get(key,"")); db.session.add(s)
                else: s.value=request.form.get(key,"")
            db.session.commit(); flash("Configuration saved.","success"); return redirect(url_for("settings"))
        vals={x.key:x.value for x in Setting.query.all()}
        vals.setdefault("minimum_contribution","100000"); vals.setdefault("share_pct","50"); vals.setdefault("social_pct","50")
        vals.setdefault("penalty_method","percentage"); vals.setdefault("penalty_rate","30"); vals.setdefault("penalty_fixed","0")
        vals.setdefault("grace_days","0"); vals.setdefault("deadline_day","30")
        return render_template("settings.html",vals=vals)
    @app.route("/transactions/<int:tid>/reverse",methods=["POST"])
    @roles_required("Administrator","Chairman")
    def reverse_transaction(tid):
        tx=db.get_or_404(Transaction,tid)
        reason=request.form.get("reason","").strip()
        if not reason: flash("A reversal reason is mandatory.","danger"); return redirect(request.referrer or url_for("reports"))
        if tx.status!="Posted": flash("Only posted transactions can be reversed.","warning")
        else:
            tx.status="Reversed"
            rev=Transaction(reference="REV-"+secrets.token_hex(6).upper(),member_id=tx.member_id,loan_id=tx.loan_id,
                period_id=tx.period_id,txn_type="Reversal",category=tx.category,amount=tx.amount,
                transaction_date=date.today(),description="Reversal of "+tx.reference,created_by=current_user().id,status="Reversal")
            db.session.add(rev)
            db.session.commit(); flash("Transaction reversed and original transaction retained with reversal status.","success")
        return redirect(request.referrer or url_for("reports"))
    @app.route("/admin/reset-operational-data",methods=["GET","POST"])
    @roles_required("Administrator")
    def reset_operational_data():
        if request.method=="POST":
            if request.form.get("confirmation")!="CLEAR ALL GROUP DATA":
                flash("Reset cancelled. Type the exact confirmation phrase to proceed.","danger")
                return redirect(url_for("reset_operational_data"))
            try:
                # Keep user accounts and group settings to avoid locking the group out.
                # Clear all member and financial/operational records only.
                Transaction.query.delete(synchronize_session=False)
                LoanInstallment.query.delete(synchronize_session=False)
                Loan.query.delete(synchronize_session=False)
                OpeningBalance.query.delete(synchronize_session=False)
                OpeningBatch.query.delete(synchronize_session=False)
                MpesaReconciliation.query.delete(synchronize_session=False)
                CashMovement.query.delete(synchronize_session=False)
                ContributionPeriod.query.delete(synchronize_session=False)
                User.query.update({User.member_id:None},synchronize_session=False)
                User.query.filter(User.role!="Administrator").update({User.active:False},synchronize_session=False)
                Member.query.delete(synchronize_session=False)
                db.session.commit()
                session.clear()
                flash("All member and operational financial data has been cleared. Administrator account(s) and group settings were retained; non-administrator accounts were deactivated.","success")
                return redirect(url_for("login"))
            except Exception as e:
                db.session.rollback(); flash(f"Reset failed; database transaction was rolled back. {e}","danger")
        return render_template("reset_data.html")

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        admin_username=os.getenv("BOOTSTRAP_ADMIN_USERNAME","admin").strip() or "admin"
        if not User.query.filter_by(username=admin_username).first():
            u=User(username=admin_username,full_name="System Administrator",role="Administrator")
            password=os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
            if not password: raise RuntimeError("Set BOOTSTRAP_ADMIN_PASSWORD before initialising the database.")
            u.set_password(password); db.session.add(u); db.session.commit()
        print("Database tables checked and administrator bootstrap completed. No placeholder members are created.")
    return app
# Expose the Flask instance for both `gunicorn app:app` and `gunicorn wsgi:app`.
app = create_app()
def excel_send(wb, filename):
    b=io.BytesIO(); wb.save(b); b.seek(0)
    return send_file(b,mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",as_attachment=True,download_name=filename)

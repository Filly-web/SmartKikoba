{% extends "base.html" %}
{% block content %}
<div class="page-heading"><div><div class="eyebrow">ADMINISTRATION</div><h2 class="page-title">Historical Loan Import Reviews</h2></div><a class="btn btn-outline-secondary btn-sm" href="{{url_for('opening')}}">Back to uploads</a></div>
<div class="alert alert-info">Imports with partial instalments or other unusual loan positions are held here. No loan or repayment transaction is posted until an Administrator approves the findings.</div>
{% for r in reviews %}
<div class="panel mb-3">
  <div class="d-flex justify-content-between align-items-start flex-wrap gap-2"><div><h5>{{r.filename}}</h5><div class="small text-muted">Submitted {{r.created_at.strftime('%d %b %Y %H:%M')}} · Review #{{r.id}}</div></div><span class="badge text-bg-{{'warning' if r.status=='Pending' else ('success' if r.status in ['Approved','Consumed'] else 'secondary')}}">{{r.status}}</span></div>
  <h6 class="mt-3">Findings requiring review</h6><ul>{% for finding in r.findings.split('\n') %}<li class="mb-2">{{finding}}</li>{% endfor %}</ul>
  {% if r.status=='Pending' %}<form method="post" action="{{url_for('approve_loan_opening_review',review_id=r.id)}}" onsubmit="return confirm('Approve these findings? The exact same workbook must then be re-uploaded to post the loan register.');"><button class="btn btn-success btn-sm">Approve findings</button></form>{% elif r.status=='Approved' %}<div class="alert alert-success mb-0">Approved. Re-upload the exact same Excel file, without editing it, to post the loan register.</div>{% elif r.status=='Consumed' %}<div class="small text-success">Approved workbook was successfully imported.</div>{% endif %}
</div>
{% else %}<div class="panel"><p class="text-muted mb-0">There are no historical loan import reviews.</p></div>{% endfor %}
{% endblock %}

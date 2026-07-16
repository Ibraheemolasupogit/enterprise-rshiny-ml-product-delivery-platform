select issue_type, count(*) as reconciled_count
from quality.data_quality_issues
group by issue_type;

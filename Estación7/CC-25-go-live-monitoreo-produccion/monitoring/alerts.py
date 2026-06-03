"""CloudWatch alarm definitions via boto3 — run once at go-live"""
import boto3

cw = boto3.client("cloudwatch", region_name="us-east-1")

ALARMS = [
    {
        "AlarmName": "CC-API-5xx-High",
        "MetricName": "5XXError",
        "Namespace": "AWS/ApiGateway",
        "Statistic": "Sum",
        "Period": 300,
        "EvaluationPeriods": 1,
        "Threshold": 10,
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "notBreaching",
    },
    {
        "AlarmName": "CC-Lambda-Duration-High",
        "MetricName": "Duration",
        "Namespace": "AWS/Lambda",
        "Statistic": "p95",
        "Period": 300,
        "EvaluationPeriods": 2,
        "Threshold": 3000,  # 3s cold start limit
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "notBreaching",
    },
    {
        "AlarmName": "CC-RDS-CPU-High",
        "MetricName": "CPUUtilization",
        "Namespace": "AWS/RDS",
        "Statistic": "Average",
        "Period": 300,
        "EvaluationPeriods": 3,
        "Threshold": 80,
        "ComparisonOperator": "GreaterThanThreshold",
        "TreatMissingData": "notBreaching",
    },
]


def create_alarms(sns_topic_arn: str):
    for alarm in ALARMS:
        cw.put_metric_alarm(
            **alarm,
            AlarmActions=[sns_topic_arn],
            OKActions=[sns_topic_arn],
        )
        print(f"Created alarm: {alarm['AlarmName']}")


if __name__ == "__main__":
    import sys
    topic_arn = sys.argv[1] if len(sys.argv) > 1 else "arn:aws:sns:us-east-1:000000000000:cc-alerts"
    create_alarms(topic_arn)

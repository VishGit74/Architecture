#!/bin/bash
# Document EC2 Setup
# Run this to capture your current AWS infrastructure

echo "=========================================="
echo "EC2 INFRASTRUCTURE DOCUMENTATION"
echo "Generated: $(date)"
echo "=========================================="

echo ""
echo "--- EC2 INSTANCES ---"
aws ec2 describe-instances \
    --query 'Reservations[*].Instances[*].[InstanceId,InstanceType,State.Name,PublicIpAddress,LaunchTime]' \
    --output table

echo ""
echo "--- SECURITY GROUPS ---"
aws ec2 describe-security-groups \
    --query 'SecurityGroups[*].[GroupId,GroupName]' \
    --output table

echo ""
echo "--- INBOUND RULES (capital-app-sg) ---"
aws ec2 describe-security-groups \
    --group-ids sg-04f46ccddb2be83fd \
    --query 'SecurityGroups[*].IpPermissions[*].[IpProtocol,FromPort,ToPort,IpRanges[0].CidrIp]' \
    --output table

echo ""
echo "--- KEY PAIRS ---"
aws ec2 describe-key-pairs \
    --query 'KeyPairs[*].[KeyName,CreateTime]' \
    --output table

echo ""
echo "=========================================="
echo "Documentation complete"
echo "=========================================="

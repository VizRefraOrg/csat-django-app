#!/usr/bin/env bash

__update_my_ip() {
    # Update a security group rule allowing your
    # current IPv4 I.P. to connect on port 22 (SSH)

    # variables to identify sec group and sec group rule
    SEC_GROUP_ID=$1
    SEC_GROUP_RULE_ID=$2
    PORT=$3

    # gets current date and prepares description for sec group rule
    CURRENT_DATE=$(date +'%Y-%m-%d')
    SEC_GROUP_RULE_DESCRIPTION="dynamic ip updated - ${CURRENT_DATE}"

    # gets current I.P. and adds /32 for ipv4 cidr
    CURRENT_IP=$(curl --silent https://checkip.amazonaws.com)
    NEW_IPV4_CIDR="${CURRENT_IP}"/32

    # updates I.P. and description in the sec group rule
    aws ec2 modify-security-group-rules \
      --group-id "${SEC_GROUP_ID}" \
      --security-group-rules SecurityGroupRuleId="${SEC_GROUP_RULE_ID}",SecurityGroupRule="{CidrIpv4=${NEW_IPV4_CIDR}, IpProtocol=tcp,FromPort=${PORT},ToPort=${PORT},Description=${SEC_GROUP_RULE_DESCRIPTION}}" >/dev/null

    # shows the sec group rule updated
    aws ec2 describe-security-group-rules \
      --filter Name="security-group-rule-id",Values="${SEC_GROUP_RULE_ID}" >/dev/null
}

__codedeploy_push() {
  aws deploy push \
    --application-name ${CODEDEPLOY_APP} \
    --s3-location s3://${CODEDEPLOY_BUCKET}/${CODEDEPLOY_APP}/${GITHUB_SHA}.zip \
    --ignore-hidden-files
}

__run_codedeploy() {

  echo "Run codedeploy ..."

  aws deploy create-deployment \
    --application-name ${CODEDEPLOY_APP} \
    --s3-location bucket=${CODEDEPLOY_BUCKET},key=${CODEDEPLOY_APP}/${GITHUB_SHA}.zip,bundleType=zip \
    --deployment-config-name CodeDeployDefault.OneAtATime \
    --deployment-group-name ${CODEDEPLOY_GROUP} \
    --file-exists-behavior OVERWRITE \
    --auto-rollback-configuration enabled=true,events=DEPLOYMENT_FAILURE \
    --description "Deploy new change of ${TF_VAR_git_branch}" > res.json

  JOB_ID=$(jq -r '.deploymentId' res.json)
  STATUS=$(aws deploy get-deployment --deployment-id $JOB_ID | jq -r '.deploymentInfo.status')
  echo "Deployment jobId: ${JOB_ID} - ${STATUS}"
  while [ $STATUS != 'Succeeded' ]
  do
     STATUS=$(aws deploy get-deployment --deployment-id $JOB_ID | jq -r '.deploymentInfo.status')
     if [ $STATUS == "Failed" ]; then
       echo "Deployment jobId: ${JOB_ID} - ${STATUS} "
       TRACE=$(aws deploy get-deployment-instance --deployment-id $JOB_ID --instance-id "${CODEDEPLOY_INSTANCE}" | jq -r '.instanceSummary.lifecycleEvents[].diagnostics | select(.errorCode | contains("ScriptFailed"))?')

       # set github output for pr comment
       echo "JOB_ID=${JOB_ID}" >> "$GITHUB_OUTPUT"
       {
        echo 'TRACE_MSG<<EOF'
        echo "$TRACE"
        echo EOF
       } >> "$GITHUB_OUTPUT"

       echo "${TRACE}"
       exit 1
     fi
     echo "Update status: ${STATUS} ..."
  done
  echo "Done"
}

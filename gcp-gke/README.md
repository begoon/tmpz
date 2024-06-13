# k8s

gcloud container clusters get-credentials autopilot-cluster --region europe-west2

kubectl expose deployment info --type=LoadBalancer --port=80 --target-port=8000

kubectl describe services

kubectl get services

kubectl get deployments
kubectl describe deployment info

kubectl get pods
watch kubectl get pods

kubectl scale deployment info --replicas=3

gcloud container clusters describe autopilot-cluster --region europe-west2

IP=$(kubectl get services info --output jsonpath='{.status.loadBalancer.ingress[0].ip}')

watch -n 1 "curl -s http://$IP | jq '.HOSTNAME, .VERSION'"

kubectl set image deployment/info info-service-container=europe-docker.pkg.dev/iproov-chiro/gke/info-service:v2

kubectl scale deployment info --replicas=5

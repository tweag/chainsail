# Setup guide for running jobs on a Kubernetes cluster
This guide describes how to set up a Kubernetes cluster for the scheduler to send jobs onto.  

## Google Kubernetes Engine
### (Optional) Provision a cluster
- **Create a cluster**
  ```bash
  gcloud container --project="resaas-simeon-dev" clusters create <cluster-name> --zone="europe-west3-c" --autoscaling-profile=optimize-utilization --cluster-ipv4-cidr=<cidr-range>(ex:"10.100.0.0/14") --machine-type="e2-small" --num-nodes=1 --enable-autoscaling --min-nodes=0 --max-nodes=3
  ```
- **Create a node pool for chainsail jobs**
  ```bash
  gcloud container --project "resaas-simeon-dev" node-pools create "pool-rexjobs" --cluster=<cluster-name> --zone="europe-west3-c" --machine-type="e2-standard-8" --disk-size="20" --node-taints="app=chainsail:NoSchedule" --enable-autoscaling --num-nodes=0 --min-nodes=0 --max-nodes=100
  ```
- **Set up firewall rules**
  ```bash
  gcloud compute firewall-rules create "gke-"<cluster-name>"-egress" --direction="egress" --action="allow" --destination-ranges=<cidr-range>(ex:"10.100.0.0/14") --rules="all"
  gcloud compute firewall-rules create "gke-"<cluster-name>"-ingress" --direction="ingress" --action="allow" --source-ranges=<cidr-range>(ex:"10.100.0.0/14") --rules="all"
  ```
- **Set up kubernetes objects**
  - Fetch the cluster credentials
  ```bash
  gcloud container clusters get-credentials <cluster-name> --zone="europe-west3-c"
  kubectl config get-contexts   # verification
  ```
  - Permission for the resaas-storage service account
  ```bash
  cd /path/to/resaas/kubernetes/
  kubectl apply -f rbac.yaml
  ```
  - (Optional) Cluster overprovisioning
  ```bash
  cd /path/to/resaas/kubernetes/
  kubectl apply -f overprovisioning.yaml
  ```

### Deploy Chainsail
- **Export the kubernetes configuration**
  ```bash
  kubectl config view --minify --flatten > /path/to/resaas/docker/kubeconfig.yaml
  ```
  This `kubeconfig.yaml` file provides the credentials for the scheduler to launch jobs onto the kubernetes cluster. It needs to be mounted into both the `scheduler` and the `celery-worker` containers. Make sure this is correctly specified in the `docker-compose.yaml` file :
   ```yaml
   # Example
   scheduler:
     # ...
     volumes:
       - ./kubeconfig.yaml:/config/kubeconfig.yaml
     environment:
       - KUBECONFIG=/config/kubeconfig.yaml
     # ...
   ```
- **Edit configuration files**
  Configure all the configuration files properly inside a `config_dpl` directory.
- **Set up the configuration files on the cluster**
  The whole `config_dpl` directory needs to be mounted as a configmap onto the cluster.
  ```bash
  kubectl create configmap config-dpl-configmap --from-file=/path/to/resaas/docker/config_dpl/
  ```
- **Launch the app**
  Finally, you can launch the app using `docker-compose`.
  ```bash
  docker-compose -f docker-compose.yaml up
  ```




## Minikube
**Disclaimer:** Instructions incomplete, don't use for now.
- **Create the cluster**
  ```bash
  minikube start
  ```
  However, be aware that minikube will create its own network at startup, named *minikube* by default (use `docker network ls` to check that). It is thus necessary to adapt the network of the scheduler in order for the latter to be able to communicate with the minikube cluster. The most simple way to arrange that is to adapt the network in the `docker-compose.yaml` file, by adding the following chunk at the end:
  ```yaml
  networks:
    default:
      name: minikube
      external: true
  ```
- **Load the pod's docker images to Minikube**
  ```bash
  minikube image load chainsail-mpi-node:dev
  minikube image load chainsail-mpi-user-code:dev
  minikube image load chainsail-mpi-httpstan-server:dev
  ```
- **Adapt image names**
  Get images names
  ```bash
  minikube image ls
  ```
  And adapt the images names in the `scheduler.yaml` file.
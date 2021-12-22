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
- **Generate the kubernetes configuration** ([source](https://cloud.google.com/kubernetes-engine/docs/how-to/api-server-authentication#environments-without-gcloud))  
  To generate a static kubeconfig file, get the `endpoint` and `clusterCaCertificate` values for your cluster
    ```bash
    # endpoint
    gcloud container clusters describe <cluster-name> --zone=europe-west3-c --format="value(endpoint)"
    # masterAuth.clusterCaCertificate
    gcloud container clusters describe <cluster-name> --zone=europe-west3-c --format="value(masterAuth.clusterCaCertificate)"
    ```
    Create a `kubeconfig.yaml` file containing the following (or modify the existing [`kubeconfig.yaml`](../docker/kubeconfig.yaml) template)
    ```yaml
    apiVersion: v1
    kind: Config
    clusters:
    - name: <cluster-name>
      cluster:
        server: https://<endpoint>
        certificate-authority-data: <masterAuth.clusterCaCertificate>
    users:
    - name: chainsail-scheduler
      user:
        auth-provider:
          name: gcp
    contexts:
    - context:
        cluster: <cluster-name>
        user: chainsail-scheduler
      name: <cluster-name>
    current-context: <cluster-name>
    ```
  This `kubeconfig.yaml` file provides the credentials for the scheduler to launch jobs onto the kubernetes cluster. It needs to be mounted into both the `scheduler` and the `celery-worker` containers. Make sure this is correctly specified in the `docker-compose.yaml` file:
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

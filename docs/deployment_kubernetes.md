# Setup guide for running jobs on a Kubernetes cluster
This guide describes how to set up a Kubernetes cluster for the scheduler to send jobs onto.  

1. **Create a cluster**
   - **GKE**  
     You can create a cluster using the GCP console or the command line SDK. Or use an existing cluster
     ```bash
     # List clusters
     gcloud container clusters list
     # Resize if needed
     gcloud container clusters resize <cluster-name> --size=<nb-nodes> --node-pool=<pool-name> --zone=<zone>
     # Get credentials
     gcloud container clusters get-credentials <cluster-name> --zone=<zone>
     ```
   - **Minikube**  
     ```bash
     # Start a minikube cluster
     minikube start
     ```
     However, be aware that minikube will create its own network at startup, named *minikube* by default. It is thus necessary to adapt the network of the scheduler in order for the latter to be able to communicate with the minikube cluster. The most simple way to arrange that is to adapt the network in the `docker-compose.yaml` file, by adding the following chunk :
     ```yaml
     networks:
       default:
         name: minikube
         external: true
     ```
2. **Create the configuration configmap onto the cluster**
   ```bash
   # Verify the current context
   kubectl config get-contexts
   # Create the configmap
   kubectl create configmap config-dpl-configmap --from-file=/path/to/resaas/docker/config_dpl/
   ```
3. **Export the Kubernetes configuration**
   ```bash
   kubectl config view --minify --flatten > /path/to/resaas/docker/kubeconfig.yaml
   ```
   This `kubeconfig` file provides the credentials for the scheduler to launch jobs onto the kubernetes cluster. It needs to be mounted into both the scheduler container and the celery container. Make sure this is correctly specified in the docker-compose file :
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

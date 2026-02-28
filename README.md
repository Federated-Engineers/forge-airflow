# forge  airflow

## OVERVIEW
This repository serves as the dedicated Airflow codebase for the `forge data engineering` team. It is the single source of truth for all DAG definitions running on the forge airflow instance deployed on Kubernetes.

All changes to this repository must be made through a `Pull Request (PR)`. Direct pushes to the main branch are strictly blocked. This process ensures full visibility into all workflow changes and deployments. Each PR must be reviewed and approved by an Engineering Lead to ensure workflows are properly designed, optimized, and production-ready before deployment to the Airflow production environment.

## REPOSITORY ARCHITECTURE

<img width="1431" height="663" alt="Screenshot 2026-02-27 at 16 23 31" src="https://github.com/user-attachments/assets/f5442518-de1f-4330-9205-15418a79cc71" />

The `Airflow DAG` deployment workflow follows these steps:

- DAG development begins in the engineer’s local branch.
- The engineer opens a `Pull Request`, which undergoes review and approval.
- Once approved and merged, the CI/CD pipeline is triggered.
- The pipeline builds a new Docker image containing the updated DAGs.
- The image is tagged and pushed to `Elastic Container Registry (ECR)`.
- The pipeline updates [this file](https://github.com/Federated-Engineers/kubernetes-deployments/blob/main/applications/production-values/forge-airflow-values.yaml#L83) in the `Kubernetes deployment` configuration repository with the new image tag.
- `ArgoCD`, our GitOps deployment tool, detects the change and automatically rolls out the updated deployment.
- `ArgoCD` manages the full lifecycle of the Airflow instance on Kubernetes.

## REPOSITORY STRUCTURE
`.github/` --->
Contains the CI/CD workflow configurations used for automated building, and deployment.

`business_logic/` --->
Contains reusable business logic modules used by DAG files. DAGs import logic from this directory to maintain clean and modular code.

`config/` --->
Contains Airflow configuration files used for local development. Production Airflow configurations are managed separately in the [forge-airflow-values.yaml](https://github.com/Federated-Engineers/kubernetes-deployments/blob/main/applications/production-values/forge-airflow-values.yaml#L2836) file.

`plugins/` --->
Contains custom Airflow plugins and shared modules that are not specific to any single DAG. This helps maintain code organization and readability.

`Dockerfile` --->
Defines the Docker image build process used by the CI/CD pipeline to package DAGs and dependencies.

`docker-compose.yaml` --->
Used only for local development and testing. It mirrors the production environment structure, allowing engineers to validate DAGs locally before submitting a Pull Request.

`requirements.txt` --->
Defines the production dependencies required for DAG execution. Add any new libraries here when developing new DAGs.

`requirements-dev.txt` --->
Contains dependencies required only for CI/CD processes, such as testing and validation tools.

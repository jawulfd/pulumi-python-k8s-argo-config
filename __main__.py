import pulumi
import pulumi_kubernetes as kubernetes
import base64
import os

config = pulumi.Config()
argo_namespace = config.get("k8sNamespace", "argo")

argo_cd_version = config.get("argoCDVersion", "argo-cd-7.7.7")
argo_events_version = config.get("argoEventsVersion", "argo-events-2.4.9")
argo_workflows_version = config.get("argoWorkflowsVersion", "argo-workflows-0.45.1")

redis_password = os.getenv('REDIS_PASSWORD')

argo_ns = kubernetes.core.v1.Namespace(
    "argo-ns",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        name=argo_namespace,
    )
)

argocd_redis_secret = kubernetes.core.v1.Secret(
    "argocd-redis-secret",
    metadata=kubernetes.meta.v1.ObjectMetaArgs(
        name='argocd-redis',
        namespace=argo_ns.metadata.name
    ),
    type="Opaque",
    data={
        "auth": str(base64.b64encode(bytes(redis_password, "utf-8"), None), "utf-8")
    }
)

argo_cd_release = kubernetes.helm.v4.Chart(
    "argo-cd",
    chart=f"https://github.com/argoproj/argo-helm/releases/download/{argo_cd_version}/{argo_cd_version}.tgz",
    namespace=argo_ns.metadata.name,
    value_yaml_files=[
        pulumi.FileAsset("resources/argo/values/argocd-values.yaml")
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[
            argocd_redis_secret
        ]
    )
)

argo_events_release = kubernetes.helm.v4.Chart(
    "argo-events",
    chart=f"https://github.com/argoproj/argo-helm/releases/download/{argo_events_version}/{argo_events_version}.tgz",
    namespace=argo_ns.metadata.name
)

argo_workflows_release = kubernetes.helm.v4.Chart(
    "argo-workflows",
    chart=f"https://github.com/argoproj/argo-helm/releases/download/{argo_workflows_version}/{argo_workflows_version}.tgz",
    namespace=argo_ns.metadata.name,
    value_yaml_files=[
        pulumi.FileAsset("resources/argo/values/argoworkflows-values.yaml")
    ]
)

argo_ingress = kubernetes.yaml.v2.ConfigGroup(
    "argo-ingress",
    files=[
        "resources/argo/ingress/argocd-ingress.yaml",
        "resources/argo/ingress/argoworkflows-ingress.yaml",
        "resources/argo/ingress/argoworkflows-middleware.yaml"
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[
            argo_cd_release,
            argo_events_release,
            argo_workflows_release
        ]
    )
)

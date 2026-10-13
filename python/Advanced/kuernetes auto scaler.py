import asyncio
import kubernetes
from kubernetes import client, watch
import json
import time
import yaml
from typing import Dict, List, Optional
import logging
import signal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomAutoScaler:
    def __init__(self, namespace: str = "default"):
        """Initialize Kubernetes auto-scaler"""
        kubernetes.config.load_incluster_config()
        self.apps_v1 = client.AppsV1Api()
        self.core_v1 = client.CoreV1Api()
        self.custom_api = client.CustomObjectsApi()
        self.namespace = namespace
        
        self.scaling_configs: Dict[str, dict] = {}
        self.scaling_history: Dict[str, List[dict]] = {}
        self.last_scale_time: Dict[str, float] = {}
        self.running = True
    
    def load_config(self, config_path: str = "scaler_config.yaml"):
        """Load scaling configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            for deployment in config.get('deployments', []):
                self.scaling_configs[deployment['name']] = {
                    'min_replicas': deployment.get('min_replicas', 1),
                    'max_replicas': deployment.get('max_replicas', 10),
                    'target_cpu': deployment.get('target_cpu_percent', 50),
                    'target_memory': deployment.get('target_memory_percent', 70),
                    'scale_up_cooldown': deployment.get('scale_up_cooldown', 60),
                    'scale_down_cooldown': deployment.get('scale_down_cooldown', 180),
                    'metric_threshold': deployment.get('metric_threshold', 0.7),
                }
            
            logger.info(f"Loaded config for {len(self.scaling_configs)} deployments")
        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")
            self.scaling_configs = {
                'default': {
                    'min_replicas': 1,
                    'max_replicas': 10,
                    'target_cpu': 50,
                    'target_memory': 70,
                    'scale_up_cooldown': 60,
                    'scale_down_cooldown': 180,
                    'metric_threshold': 0.7
                }
            }
    
    async def get_deployment_metrics(self, deployment_name: str) -> dict:
        """Get metrics for a specific deployment"""
        try:
            # Get pods for this deployment
            deployment = self.apps_v1.read_namespaced_deployment(deployment_name, self.namespace)
            selector = f"app={deployment_name}"
            
            pods = self.core_v1.list_namespaced_pod(
                self.namespace,
                label_selector=selector
            )
            
            total_cpu = 0
            total_memory = 0
            total_pods = 0
            
            for pod in pods.items:
                # Get pod metrics from Kubernetes metrics API
                try:
                    metrics = self.custom_api.get_namespaced_custom_object(
                        group="metrics.k8s.io",
                        version="v1beta1",
                        namespace=self.namespace,
                        plural="pods",
                        name=pod.metadata.name
                    )
                    
                    cpu_usage = 0
                    memory_usage = 0
                    
                    for container in metrics.get('containers', []):
                        cpu_usage += self._parse_quantity(container.get('usage', {}).get('cpu', '0'))
                        memory_usage += self._parse_quantity(container.get('usage', {}).get('memory', '0'))
                    
                    total_cpu += cpu_usage
                    total_memory += memory_usage
                    total_pods += 1
                except:
                    pass
            
            # Get resource limits for capacity calculation
            resources = deployment.spec.template.spec.containers[0].resources
            cpu_limit = self._parse_quantity(resources.limits.get('cpu', '100m'))
            memory_limit = self._parse_quantity(resources.limits.get('memory', '128Mi'))
            
            avg_cpu_percent = (total_cpu / (cpu_limit * total_pods)) * 100 if total_pods > 0 else 0
            avg_memory_percent = (total_memory / (memory_limit * total_pods)) * 100 if total_pods > 0 else 0
            
            return {
                'name': deployment_name,
                'replicas': deployment.spec.replicas,
                'available_replicas': deployment.status.available_replicas or 0,
                'cpu_usage_percent': avg_cpu_percent,
                'memory_usage_percent': avg_memory_percent,
                'cpu_limit': cpu_limit,
                'memory_limit': memory_limit,
                'pod_count': total_pods
            }
        except Exception as e:
            logger.error(f"Error getting metrics for {deployment_name}: {e}")
            return None
    
    def _parse_quantity(self, value: str) -> float:
        """Parse Kubernetes quantity to float"""
        try:
            if value.endswith('m'):
                return float(value[:-1]) / 1000
            elif value.endswith('Ki'):
                return float(value[:-2]) * 1024
            elif value.endswith('Mi'):
                return float(value[:-2]) * 1024 * 1024
            elif value.endswith('Gi'):
                return float(value[:-2]) * 1024 * 1024 * 1024
            else:
                return float(value)
        except:
            return 0
    
    async def calculate_scaling_decision(self, deployment_name: str, metrics: dict) -> tuple:
        """Calculate whether to scale up, down, or maintain"""
        config = self.scaling_configs.get(deployment_name)
        if not config:
            config = self.scaling_configs.get('default', {})
        
        if not metrics:
            return 'maintain', 0
        
        current_replicas = metrics['replicas']
        cpu_percent = metrics.get('cpu_usage_percent', 0)
        memory_percent = metrics.get('memory_usage_percent', 0)
        
        # Calculate desired replicas based on CPU
        target_cpu = config.get('target_cpu', 50)
        if cpu_percent > 0 and target_cpu > 0:
            desired_cpu_replicas = int((cpu_percent / target_cpu) * current_replicas)
        else:
            desired_cpu_replicas = current_replicas
        
        # Calculate desired replicas based on Memory
        target_memory = config.get('target_memory', 70)
        if memory_percent > 0 and target_memory > 0:
            desired_memory_replicas = int((memory_percent / target_memory) * current_replicas)
        else:
            desired_memory_replicas = current_replicas
        
        # Use the maximum of the two
        desired_replicas = max(desired_cpu_replicas, desired_memory_replicas)
        
        # Apply limits
        min_replicas = config.get('min_replicas', 1)
        max_replicas = config.get('max_replicas', 10)
        desired_replicas = max(min_replicas, min(max_replicas, desired_replicas))
        
        # Check cooldown periods
        last_scale = self.last_scale_time.get(deployment_name, 0)
        cooldown = config.get('scale_down_cooldown' if desired_replicas < current_replicas else 'scale_up_cooldown', 60)
        
        if time.time() - last_scale < cooldown:
            return 'maintain', current_replicas
        
        if desired_replicas > current_replicas:
            return 'scale_up', desired_replicas
        elif desired_replicas < current_replicas:
            return 'scale_down', desired_replicas
        else:
            return 'maintain', current_replicas
    
    async def apply_scale(self, deployment_name: str, decision: str, target_replicas: int):
        """Apply scaling decision to the deployment"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(deployment_name, self.namespace)
            
            if decision == 'scale_up' or decision == 'scale_down':
                deployment.spec.replicas = target_replicas
                self.apps_v1.patch_namespaced_deployment(deployment_name, self.namespace, deployment)
                
                self.last_scale_time[deployment_name] = time.time()
                
                logger.info(f"Scaled {deployment_name} to {target_replicas} replicas ({decision})")
                
                # Log scaling event
                if deployment_name not in self.scaling_history:
                    self.scaling_history[deployment_name] = []
                
                self.scaling_history[deployment_name].append({
                    'timestamp': time.time(),
                    'decision': decision,
                    'replicas': target_replicas
                })
                
                # Keep only last 100 entries
                if len(self.scaling_history[deployment_name]) > 100:
                    self.scaling_history[deployment_name] = self.scaling_history[deployment_name][-100:]
        except Exception as e:
            logger.error(f"Error scaling {deployment_name}: {e}")
    
    async def run_scaling_loop(self):
        """Main scaling loop"""
        logger.info("Starting auto-scaling loop")
        
        while self.running:
            for deployment_name in self.scaling_configs:
                try:
                    # Get metrics
                    metrics = await self.get_deployment_metrics(deployment_name)
                    
                    if metrics:
                        # Calculate scaling decision
                        decision, target_replicas = await self.calculate_scaling_decision(deployment_name, metrics)
                        
                        # Apply scaling if needed
                        if decision != 'maintain':
                            await self.apply_scale(deployment_name, decision, target_replicas)
                        
                        logger.debug(f"{deployment_name}: CPU={metrics['cpu_usage_percent']:.1f}%, "
                                   f"Memory={metrics['memory_usage_percent']:.1f}%, "
                                   f"Replicas={metrics['replicas']}, Decision={decision}")
                except Exception as e:
                    logger.error(f"Error processing {deployment_name}: {e}")
            
            # Sleep before next iteration
            await asyncio.sleep(30)
    
    async def run_health_check(self):
        """Run health checks on deployments"""
        while self.running:
            for deployment_name in self.scaling_configs:
                try:
                    deployment = self.apps_v1.read_namespaced_deployment(deployment_name, self.namespace)
                    
                    # Check for unhealthy pods
                    if deployment.status.unavailable_replicas and deployment.status.unavailable_replicas > 0:
                        logger.warning(f"Unavailable replicas for {deployment_name}: "
                                     f"{deployment.status.unavailable_replicas}")
                    
                    # Check if deployment is healthy
                    ready = deployment.status.ready_replicas or 0
                    desired = deployment.spec.replicas or 0
                    
                    if ready < desired * 0.5:
                        logger.warning(f"{deployment_name} has low readiness: {ready}/{desired}")
                except Exception as e:
                    logger.error(f"Health check error for {deployment_name}: {e}")
            
            await asyncio.sleep(60)
    
    async def run(self):
        """Start the auto-scaler"""
        try:
            # Load configuration
            self.load_config()
            
            # Create tasks
            scaling_task = asyncio.create_task(self.run_scaling_loop())
            health_task = asyncio.create_task(self.run_health_check())
            
            # Wait for tasks
            await asyncio.gather(scaling_task, health_task)
        except asyncio.CancelledError:
            self.running = False
            logger.info("Auto-scaler stopped")

async def main():
    scaler = CustomAutoScaler()
    
    # Handle shutdown
    def signal_handler():
        scaler.running = False
    
    signal.signal(signal.SIGINT, lambda s, f: signal_handler())
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler())
    
    print("=== Kubernetes Auto-Scaler ===")
    print("Monitoring deployments and auto-scaling")
    print("Config: scaler_config.yaml")
    
    await scaler.run()

if __name__ == "__main__":
    asyncio.run(main())

# scaler_config.yaml example:
# deployments:
#   - name: web-app
#     min_replicas: 2
#     max_replicas: 10
#     target_cpu_percent: 50
#     target_memory_percent: 70
#     scale_up_cooldown: 60
#     scale_down_cooldown: 180
#   - name: worker-app
#     min_replicas: 1
#     max_replicas: 5
#     target_cpu_percent: 60
#     target_memory_percent: 80
#
# Install: pip install kubernetes pyyaml
# Run in Kubernetes cluster with service account permissions
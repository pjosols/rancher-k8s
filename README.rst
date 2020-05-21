===========================================
rancher-k8s
===========================================

This playbook deploys Kubernetes via the Rancher API.  It requires a custom node driver for interacting with
a private machine orchestration layer, but maybe some parts of it are useful to others.



Command
===============

::

    ansible-playbook -i inventory/nonprod kubernetes.yaml



Sample config file
==================

::

    ---
    # Group specific information
    group: Dev                       # same as group for eportal token user

    # Cluster details
    cluster_name: pauls-test-cluster
    region: NYC01
    network: "10.10.10.0/24 (UAT1)"  # exactly as it appears in eportal

    # Dynamic Volume Provisioning
    enable_dvp: yes
    dvp_volume_size: 20G             # optional, required if enable_dvp is true

    # Providers
    cni_provider: calico
    ingress_provider: nginx
    kubernetes_version: v1.14.6-rancher1-1

    # Node specs
    cluster_nodes:
      master:
        cpu: 2
        memory: 2
        disk: 20
        prefix: nycdc01test50
        quantity: 1
        controlplane: yes
        etcd: yes
        worker: no
      worker:
        cpu: 2
        memory: 2
        disk: 20
        prefix: nycdc01test60
        quantity: 1
        controlplane: no
        etcd: no
        worker: yes
      couchbase:
        cpu: 2
        memory: 2
        disk: 20
        prefix: nycdc01test70
        quantity: 1
        controlplane: no
        etcd: no
        worker: yes
        labels:
          pool-couchbase: true





Author Information
==================

Paul Olsen  -- Rancher modules and tasks

Sam Chen -- DVP tasks



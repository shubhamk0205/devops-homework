# Task 1 - Kubernetes Volumes

In this task I learned how storage works in Kubernetes. A container's filesystem is temporary - if the container restarts, everything written inside it is lost. Volumes solve this problem. I tried every type on my minikube cluster (`default` namespace) and pasted the real output below.

The 6 topics:

| # | Topic | Lives as long as | Example file |
|---|-------|------------------|--------------|
| 1 | emptyDir | the Pod | `emptydir-pod.yaml` |
| 2 | hostPath | the Node | `hostpath-pod.yaml` |
| 3 | PersistentVolume (PV) | until admin deletes it (depends on reclaim policy) | `pv.yaml` |
| 4 | PersistentVolumeClaim (PVC) | until user deletes it | `pvc.yaml`, `pvc-pod.yaml` |
| 5 | StorageClass | cluster object | (`standard` already exists in minikube) |
| 6 | Dynamic provisioning | PV is auto created/deleted with the PVC | `dynamic-pvc.yaml`, `dynamic-pod.yaml` |

```text
 Ephemeral storage                    Persistent storage
 -----------------                    ------------------
 +---------- Pod ----------+          +-------- Pod --------+
 | [container]  [container]|          |    [container]      |
 |       \        /        |          |         |           |
 |      emptyDir volume    |          |        PVC  (request: "I need 500Mi")
 +-------------------------+          +---------|-----------+
   deleted with the Pod                         | bound
                                                v
                                       PV (actual storage, 1Gi)
                                                ^
                                                | creates automatically
                                       StorageClass (dynamic provisioning)
```

---

## 1. emptyDir

**What it is:** an empty folder that Kubernetes creates when the Pod is scheduled on a node. All containers in the Pod can mount it, so it is good for sharing files between containers (sidecar pattern) or for scratch/cache space. When the Pod is deleted, the emptyDir is deleted too.

My example (`emptydir-pod.yaml`) has 2 containers. `writer` (busybox) writes the date into `/shared/log.txt` every 5 seconds. `reader` (nginx) mounts the same volume at `/usr/share/nginx/html`.

```yaml
  volumes:
    - name: shared-data
      emptyDir: {}
```

```bash
kubectl apply -f emptydir-pod.yaml
kubectl get pod emptydir-demo
```
```text
pod/emptydir-demo created
NAME            READY   STATUS    RESTARTS   AGE
emptydir-demo   2/2     Running   0          55s
```

Read the file from the **other** container:
```bash
kubectl exec emptydir-demo -c reader -- cat /usr/share/nginx/html/log.txt
```
```text
Wed Oct  7 18:45:23 UTC 2026
Wed Oct  7 18:45:28 UTC 2026
Wed Oct  7 18:45:33 UTC 2026
Wed Oct  7 18:45:38 UTC 2026
Wed Oct  7 18:45:43 UTC 2026
Wed Oct  7 18:45:48 UTC 2026
Wed Oct  7 18:45:53 UTC 2026
Wed Oct  7 18:45:58 UTC 2026
```

```bash
kubectl describe pod emptydir-demo | grep -A3 '^Volumes:'
```
```text
Volumes:
  shared-data:
    Type:       EmptyDir (a temporary directory that shares a pod's lifetime)
    Medium:     
```

Now delete the Pod and create it again:
```bash
kubectl delete pod emptydir-demo
kubectl apply -f emptydir-pod.yaml
kubectl wait --for=condition=Ready pod/emptydir-demo --timeout=60s
kubectl exec emptydir-demo -c reader -- cat /usr/share/nginx/html/log.txt
```
```text
pod "emptydir-demo" deleted from default namespace
pod/emptydir-demo created
pod/emptydir-demo condition met
Wed Oct  7 18:46:34 UTC 2026
```

What I observed:
- The reader container could see the file written by the writer container, so emptyDir is shared inside the Pod.
- After deleting the Pod, the old 8 lines were gone and the file started fresh. emptyDir = same lifetime as the Pod.

---

## 2. hostPath

**What it is:** mounts a file or folder from the **node's** filesystem into the Pod. Data stays even if the Pod is deleted, but it is tied to that one node. If the Pod moves to another node, it will see a different (empty) folder. It is also a security risk (Pod can read node files), so it is mostly used for system Pods (log agents, etc.) or single node test clusters like minikube.

```yaml
  volumes:
    - name: host-storage
      hostPath:
        path: /tmp/hostpath-data
        type: DirectoryOrCreate
```

```bash
kubectl apply -f hostpath-pod.yaml
kubectl wait --for=condition=Ready pod/hostpath-demo --timeout=60s
kubectl exec hostpath-demo -- sh -c 'echo hello-from-pod > /data/note.txt'
minikube ssh -- cat /tmp/hostpath-data/note.txt
```
```text
pod/hostpath-demo created
pod/hostpath-demo condition met
hello-from-pod
```

Delete the Pod and check the node folder:
```bash
kubectl delete pod hostpath-demo
minikube ssh -- ls -l /tmp/hostpath-data
```
```text
pod "hostpath-demo" deleted from default namespace
total 4
-rw-r--r-- 1 root root 15 Oct  7 18:46 note.txt
```

Recreate the Pod and read the file:
```bash
kubectl apply -f hostpath-pod.yaml && kubectl wait --for=condition=Ready pod/hostpath-demo --timeout=60s
kubectl exec hostpath-demo -- cat /data/note.txt
```
```text
pod/hostpath-demo created
pod/hostpath-demo condition met
hello-from-pod
```

What I observed:
- The file written inside the Pod was visible directly on the minikube node with `minikube ssh`.
- The file survived Pod deletion because it lives on the node, not in the Pod.

---

## 3. PersistentVolume (PV)

**What it is:** a piece of storage in the cluster, created by an admin (static) or by a StorageClass (dynamic). It is a cluster level object (no namespace). Important fields:
- `capacity` - size of the volume
- `accessModes` - `ReadWriteOnce` (RWO, one node), `ReadOnlyMany` (ROX), `ReadWriteMany` (RWX), `ReadWriteOncePod`
- `persistentVolumeReclaimPolicy` - what happens after the claim is deleted: `Retain` (keep data, admin cleans up) or `Delete` (delete storage)
- `storageClassName` - I used `manual` here so this PV does not get mixed up with minikube's default `standard` class

```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: student-pv
spec:
  storageClassName: manual
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  persistentVolumeReclaimPolicy: Retain
  hostPath:
    path: /tmp/student-data
```

```bash
kubectl apply -f pv.yaml
kubectl get pv student-pv
```
```text
persistentvolume/student-pv created
NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS      CLAIM   STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
student-pv   1Gi        RWO            Retain           Available           manual         <unset>                          0s
```

What I observed: the PV status is `Available` because no one has claimed it yet.

---

## 4. PersistentVolumeClaim (PVC)

**What it is:** a request for storage made by the user/developer ("I need 500Mi, RWO"). Kubernetes finds a matching PV and **binds** them 1-to-1. The Pod then uses the PVC name, not the PV. This way the developer does not need to know where the storage actually is.

```text
  Pod  --uses-->  PVC (student-pvc, wants 500Mi)  --bound to-->  PV (student-pv, 1Gi)  -->  /tmp/student-data on node
```

```bash
kubectl apply -f pvc.yaml
kubectl get pvc student-pvc
kubectl get pv student-pv
```
```text
persistentvolumeclaim/student-pvc created
NAME          STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
student-pvc   Pending                                      manual         <unset>                 1s

NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                 STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
student-pv   1Gi        RWO            Retain           Bound    default/student-pvc   manual         <unset>                          1s
```

Use the PVC in a Pod (`pvc-pod.yaml`), write data, delete the Pod, create it again:
```bash
kubectl apply -f pvc-pod.yaml && kubectl wait --for=condition=Ready pod/storage-demo --timeout=60s
kubectl exec storage-demo -- sh -c 'echo saved-on-pv > /data/file.txt && cat /data/file.txt'
kubectl delete pod storage-demo
kubectl apply -f pvc-pod.yaml && kubectl wait --for=condition=Ready pod/storage-demo --timeout=60s
kubectl exec storage-demo -- cat /data/file.txt
```
```text
pod/storage-demo created
pod/storage-demo condition met
saved-on-pv
pod "storage-demo" deleted from default namespace
pod/storage-demo created
pod/storage-demo condition met
saved-on-pv
```

```bash
kubectl get pvc
```
```text
NAME          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
dynamic-pvc   Bound    pvc-00e027a7-b1b2-45de-8882-3ae2fded4d1e   500Mi      RWO            standard       <unset>                 6s
student-pvc   Bound    student-pv                                 1Gi        RWO            manual         <unset>                 9s
```

What I observed:
- The PVC was `Pending` for a moment and then the PV went to `Bound` with `CLAIM default/student-pvc`.
- I asked for 500Mi but the PVC shows **1Gi** capacity, because it got the whole PV (a PV can only be bound to one PVC).
- Data `saved-on-pv` survived the Pod being deleted and recreated.

---

## 5. StorageClass

**What it is:** a "type" or "template" of storage. It says which **provisioner** creates the disks (AWS EBS, GCE PD, minikube-hostpath, ...), the reclaim policy and the binding mode. A cluster can have many classes (e.g. `fast-ssd`, `cheap-hdd`) and one of them is the default. A PVC picks one with `storageClassName`.

```bash
kubectl get storageclass
kubectl describe storageclass standard
```
```text
NAME                 PROVISIONER                RECLAIMPOLICY   VOLUMEBINDINGMODE   ALLOWVOLUMEEXPANSION   AGE
standard (default)   k8s.io/minikube-hostpath   Delete          Immediate           false                  5m35s

Name:            standard
IsDefaultClass:  Yes
...
Provisioner:           k8s.io/minikube-hostpath
Parameters:            <none>
AllowVolumeExpansion:  <unset>
MountOptions:          <none>
ReclaimPolicy:         Delete
VolumeBindingMode:     Immediate
Events:                <none>
```

What I observed: minikube has one class `standard` which is the default. Its provisioner is `k8s.io/minikube-hostpath`, reclaim policy is `Delete`, and binding mode `Immediate` (PV is created as soon as the PVC is created, not waiting for a Pod; the other option is `WaitForFirstConsumer`).

---

## 6. Dynamic provisioning

**What it is:** with static PVs the admin must create PVs by hand before anyone can use them. With dynamic provisioning the user only creates a PVC with a `storageClassName`, and the StorageClass's provisioner **creates the PV automatically**. This is how it works in real clouds (a new EBS disk is created for each PVC).

```text
 Static:   admin creates PV  -->  user creates PVC  -->  bind
 Dynamic:  user creates PVC  -->  StorageClass provisioner creates PV  -->  bind
```

```bash
kubectl apply -f dynamic-pvc.yaml
kubectl get pvc dynamic-pvc
kubectl get pv
```
```text
persistentvolumeclaim/dynamic-pvc created
NAME          STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
dynamic-pvc   Bound    pvc-00e027a7-b1b2-45de-8882-3ae2fded4d1e   500Mi      RWO            standard       <unset>                 0s

NAME                                       CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                 STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pvc-00e027a7-b1b2-45de-8882-3ae2fded4d1e   500Mi      RWO            Delete           Bound    default/dynamic-pvc   standard       <unset>                          0s
student-pv                                 1Gi        RWO            Retain           Bound    default/student-pvc   manual         <unset>                          3s
```

```bash
kubectl apply -f dynamic-pod.yaml && kubectl wait --for=condition=Ready pod/dynamic-demo --timeout=60s
kubectl exec dynamic-demo -- df -h /data
```
```text
pod/dynamic-demo created
pod/dynamic-demo condition met
Filesystem      Size  Used Avail Use% Mounted on
/dev/vda1       911G  275G  590G  32% /data
```

What I observed:
- I never wrote a PV for `dynamic-pvc`, but a PV named `pvc-00e027a7-...` was created instantly with exactly 500Mi.
- `df` shows the full node disk because minikube-hostpath is just a folder on the node, it does not enforce the size limit. A real cloud disk would show 500Mi.

---

## Reclaim policy: Retain vs Delete (cleanup)

```bash
kubectl delete pod storage-demo dynamic-demo hostpath-demo
kubectl delete pvc dynamic-pvc student-pvc
kubectl get pv
```
```text
pod "storage-demo" deleted from default namespace
pod "dynamic-demo" deleted from default namespace
Error from server (NotFound): pods "hostpath-demo" not found
persistentvolumeclaim "dynamic-pvc" deleted from default namespace
persistentvolumeclaim "student-pvc" deleted from default namespace
NAME         CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS     CLAIM                 STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
student-pv   1Gi        RWO            Retain           Released   default/student-pvc   manual         <unset>                          14s
```
(`hostpath-demo` was already deleted earlier, so that error is fine.)

What I observed:
- The dynamic PV (policy `Delete`) disappeared together with its PVC.
- `student-pv` (policy `Retain`) stayed in `Released` state - the data is kept and an admin has to clean it up manually. So I deleted it by hand:

```bash
kubectl delete pv student-pv
minikube ssh -- sudo rm -rf /tmp/hostpath-data /tmp/student-data; echo cleaned
```
```text
persistentvolume "student-pv" deleted
cleaned
```

---

## What I learned
- **emptyDir** - temporary, shared between containers of one Pod, deleted with the Pod.
- **hostPath** - folder on the node, survives Pod deletion but tied to one node; avoid in real apps.
- **PV** - the actual storage, cluster scoped, has capacity / access mode / reclaim policy.
- **PVC** - the user's request for storage; Pods use the PVC, and it binds 1-to-1 with a PV.
- **StorageClass** - describes which provisioner makes the storage and with what settings.
- **Dynamic provisioning** - PVC + StorageClass = PV is created automatically, no admin work needed.

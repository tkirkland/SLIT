# ZFS Best Practices Guide

## Introduction

This guide covers comprehensive best practices for OpenZFS deployment, configuration, and maintenance. Following these guidelines will help ensure optimal performance, reliability, and maintainability of your ZFS storage systems.

## Hardware Requirements and Recommendations

### Memory Requirements
- **Minimum**: 8GB RAM for best performance
- **Recommended**: Use as much RAM as possible within budget constraints
- **ECC Memory**: Highly recommended due to ZFS's intensive memory usage and in-memory data caching
- **ARC Cache**: ZFS automatically dedicates available memory to ARC (Adaptive Replacement Cache)

### Storage Devices
- **Use whole disks** rather than partitions when creating pools for optimal performance and alignment
- **Consistent disk sizes**: Don't mix disks of various sizes in the same RAID vdev to avoid space loss
- **Consistent disk speeds**: Don't mix disks of different speeds in the same RAID vdev as the slowest disk becomes the bottleneck
- **Enterprise-class SSDs**: Use enterprise-grade SSDs for cache (L2ARC) and log (ZIL) devices

### Controllers and Connectivity
- **Balance disks across controllers**: Distribute disks evenly across available controllers to avoid controller bottlenecks
- **Direct disk access**: Avoid hardware RAID controllers; use HBA (Host Bus Adapter) cards in IT mode
- **Multiple controllers**: Use multiple controllers to improve overall throughput

## Pool Creation and Configuration

### Basic Pool Creation
```bash
# Create pool with optimal settings
zpool create -o ashift=12 poolname raidz2 disk1 disk2 disk3 disk4

# Create pool with compression enabled
zpool create -o ashift=12 -O compression=lz4 poolname mirror disk1 disk2
```

### ashift Configuration
- **Critical setting**: ashift must be set correctly at pool creation time and cannot be changed later
- **ashift=12**: Use for 4K sector drives (most modern drives)
- **ashift=9**: Use for genuine 512-byte sector drives (older drives)
- **Detection issues**: Many 4K drives report 512-byte sectors for compatibility; verify actual sector size
- **Performance impact**: Incorrect ashift can cause severe performance degradation due to read-modify-write operations

```bash
# Check drive sector size
fdisk -l /dev/sdX

# Create pool with explicit ashift
zpool create -o ashift=12 poolname raidz2 disk1 disk2 disk3 disk4

# Verify ashift setting
zdb -C poolname | grep ashift
```

### Device Naming
- **Production**: Use `/dev/disk/by-id/` for stability and clarity
- **Development/Testing**: `/dev/sdX` is acceptable for temporary setups
- **Avoid**: `/dev/disk/by-uuid/` as it's not practical for multi-disk pools

## RAID Configuration Best Practices

### RAID-Z Configuration
- **RAID-Z1**: 3-disk minimum, suitable for non-critical data
- **RAID-Z2**: 6-disk optimal, good balance of performance and redundancy
- **RAID-Z3**: 9-disk optimal, maximum redundancy
- **Stripe width**: Use fewer disks per stripe for better IOPS, more disks for better space efficiency

### Mirror Configuration
- **Performance**: Superior random IOPS compared to RAID-Z
- **Resilience**: Can survive multiple drive failures if they're in different mirrors
- **Scaling**: Read performance scales with number of drives per mirror

### Topology Guidelines
- **Don't mix RAID types** in the same pool (e.g., don't combine mirrors and RAID-Z)
- **Consistent vdev sizes** for optimal performance and space utilization
- **Consider workload**: Mirrors for high IOPS, RAID-Z for sequential throughput

## Compression and Deduplication

### Compression (Recommended)
```bash
# Enable LZ4 compression (default recommendation)
zfs set compression=lz4 poolname

# For rarely accessed data, consider higher compression
zfs set compression=gzip-6 poolname/archive

# Zstandard compression (OpenZFS 2.0+)
zfs set compression=zstd poolname
```

**Compression Benefits**:
- Reduces storage usage
- Can improve performance due to reduced I/O
- LZ4 provides good balance of compression ratio and speed
- Zstandard offers wide range of performance/compression trade-offs

### Deduplication (Use with Caution)
```bash
# Enable deduplication (requires significant RAM)
zfs set dedup=on poolname
```

**Deduplication Considerations**:
- Requires substantial RAM (5GB+ per TB of unique data)
- Can severely impact performance if insufficient RAM
- Consider alternatives like compression first
- Monitor DDT (Deduplication Table) size regularly

## Performance Tuning

### Record Size Optimization
```bash
# Database workloads (small random I/O)
zfs set recordsize=8K poolname/database

# Large file storage (videos, backups)
zfs set recordsize=1M poolname/media

# Default recordsize is 128K (suitable for most workloads)
```

### Special Devices (Metadata SSDs)
```bash
# Add special device for metadata
zpool add poolname special mirror ssd1 ssd2

# Set small blocks to use special device
zfs set special_small_blocks=32K poolname
```

### Cache and Log Devices
```bash
# Add L2ARC cache device
zpool add poolname cache ssd1

# Add dedicated ZIL log device
zpool add poolname log mirror ssd1 ssd2
```

### ARC Tuning
```bash
# Set maximum ARC size (in bytes)
echo "options zfs zfs_arc_max=17179869184" >> /etc/modprobe.d/zfs.conf

# Set minimum ARC size
echo "options zfs zfs_arc_min=2147483648" >> /etc/modprobe.d/zfs.conf
```

## Snapshot Management

### Snapshot Best Practices
```bash
# Create snapshot
zfs snapshot poolname/dataset@snapshot_name

# Recursive snapshot of all datasets
zfs snapshot -r poolname@snapshot_name

# Automated snapshot management with sanoid
apt install sanoid
```

### Snapshot Retention Strategy
- **Frequent snapshots**: Every 15 minutes for active data
- **Daily snapshots**: Keep for 1 month
- **Weekly snapshots**: Keep for 1 year
- **Monthly snapshots**: Keep for several years
- **Use automated tools**: sanoid for snapshot orchestration

## Backup and Replication

### ZFS Send/Receive
```bash
# Initial full backup
zfs send poolname/dataset@snapshot | ssh remote "zfs receive backup/dataset"

# Incremental backup
zfs send -i poolname/dataset@old poolname/dataset@new | ssh remote "zfs receive backup/dataset"

# Recursive replication with syncoid
syncoid -r source_pool remote_host:backup_pool
```

### Backup Strategy
- **3-2-1 Rule**: 3 copies, 2 different media, 1 offsite
- **Regular testing**: Verify backup integrity regularly
- **Automated replication**: Use tools like syncoid for automated backups
- **Separate failure domains**: Keep backups physically separated from source

## Monitoring and Maintenance

### Regular Monitoring
```bash
# Pool status and health
zpool status

# Pool I/O statistics
zpool iostat -v 5

# ARC statistics
arcstat 5

# Scrub pools regularly
zpool scrub poolname
```

### Maintenance Schedule
- **Daily**: Monitor pool status and alerts
- **Weekly**: Check pool capacity and performance metrics
- **Monthly**: Review snapshot retention and cleanup
- **Quarterly**: Perform comprehensive pool scrub
- **Annually**: Review hardware health and plan upgrades

### Capacity Management
- **Keep free space above 10%** to maintain optimal performance
- **Monitor metaslab fragmentation** with `zdb -mmm poolname`
- **Plan for growth**: Consider expansion strategy before reaching 80% capacity

## Security Best Practices

### Access Control
```bash
# Set dataset permissions
zfs allow user create,mount,snapshot poolname/dataset

# Disable setuid
zfs set setuid=off poolname/dataset

# Enable access time updates only when needed
zfs set atime=off poolname/dataset
```

### Encryption (OpenZFS 2.0+)
```bash
# Create encrypted dataset
zfs create -o encryption=on -o keyformat=passphrase poolname/encrypted

# Load key
zfs load-key poolname/encrypted

# Unload key
zfs unload-key poolname/encrypted
```

## Common Pitfalls to Avoid

### Configuration Mistakes
- **Never use ashift=9 on 4K drives** unless you understand the performance implications
- **Don't mix different vdev types** in the same pool
- **Avoid using partitions** instead of whole disks
- **Don't ignore disk alignment** when using partitions

### Operational Mistakes
- **Don't rely solely on RAID-Z for backup** - it's redundancy, not backup
- **Don't fill pools beyond 80%** without monitoring performance closely
- **Don't enable deduplication** without sufficient RAM
- **Don't ignore scrub errors** - investigate and resolve immediately

### Performance Mistakes
- **Don't use too many disks in RAID-Z** if you need high IOPS
- **Don't ignore controller bandwidth** when planning disk layout
- **Don't forget to enable compression** - LZ4 is almost always beneficial
- **Don't set recordsize arbitrarily** - match it to your workload

## Ubuntu-Specific Installation

### Installation
```bash
# Update package lists
apt update

# Install ZFS utilities
apt install zfsutils-linux

# Load ZFS module
modprobe zfs

# Verify installation
zpool version
zfs version
```

### System Integration
```bash
# Enable ZFS services
systemctl enable zfs-import-cache
systemctl enable zfs-import-scan
systemctl enable zfs-mount
systemctl enable zfs-share

# Configure automatic imports
zpool set cachefile=/etc/zfs/zpool.cache poolname
```

## Conclusion

Following these best practices will help ensure your ZFS deployment is reliable, performant, and maintainable. Remember that ZFS is a powerful but complex system - invest time in understanding its behavior and monitoring its performance. Regular maintenance, proper configuration, and automated backups are key to a successful ZFS deployment.

For additional information, consult the official OpenZFS documentation and consider engaging with the ZFS community for support and advanced configurations.
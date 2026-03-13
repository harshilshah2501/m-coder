# Backup Recovery Checklist

## Current Situation
- Qdrant collection `motadata_code` is missing (empty collections directory)
- Neo4j database exists but may be empty
- v15 model is deployed and running
- All services are ready except RAG API (waiting for Qdrant collection)

## Files to Look For in Local Backups

### QDRANT BACKUPS (Priority: HIGH)
Look for these files/directories:

**Collection Backup Files:**
- `motadata_code.tar.gz` - Complete collection backup
- `motadata_code.zip` - Zipped collection
- `qdrant_backup.tar.gz` - Full Qdrant backup
- `qdrant_collection_motadata_code.tar.gz` - Named collection backup
- `qdrant_snapshot_*.tar` - Qdrant snapshot files
- `motadata_code/` - Directory containing collection files

**Expected Structure if Found:**
```
motadata_code/
├── collection_meta.json
├── config.json
├── payload_index/
├── vectors/
└── *.db files
```

### NEO4J BACKUPS (Priority: MEDIUM)
Look for these files:

**Database Backup Files:**
- `neo4j_backup.tar.gz` - Full Neo4j backup
- `neo4j_databases.tar.gz` - Databases directory backup
- `motadata.db.tar.gz` - Motadata database backup
- `neo4j_dump.tar.gz` - Neo4j dump
- `neo4j_data/` - Directory containing database files

**Expected Structure if Found:**
```
neo4j_data/
├── databases/
│   ├── system/
│   └── neo4j/
├── dbms/
└── logs/
```

### ALTERNATIVE: EXPORT FILES
- `motadata_code.json` - JSON export of collection
- `motadata_code.jsonl` - JSONL export (one vector per line)
- `neo4j_export.cypher` - Neo4j Cypher export
- `neo4j_export.json` - Neo4j JSON export

## Restore Procedure (Once Files Found)

### For Qdrant:
1. Extract backup to `/var/lib/docker/volumes/docker_qdrant_storage/_data/collections/motadata_code/`
2. Restart Qdrant container: `docker restart qdrant-motadata`
3. Verify: `curl http://localhost:6333/collections/motadata_code`

### For Neo4j:
1. Stop Neo4j: `docker stop neo4j-motadata`
2. Extract backup to `/var/lib/docker/volumes/docker_neo4j_data/_data/`
3. Restart Neo4j: `docker start neo4j-motadata`
4. Verify: `curl http://localhost:7474`

## If No Backups Found
We will need to re-index the Motadata codebase:
- Source location: `/home/harshil/TestMotadataProject/Motadata/motadata`
- 484 Java files to index
- Estimated time: 5-10 minutes
- Script: `rag/scripts/index_motadata_codebase.py`

---
**Please check your local backups and let me know what you find!**


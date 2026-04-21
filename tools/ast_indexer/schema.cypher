CREATE CONSTRAINT class_qualified_name IF NOT EXISTS
  FOR (c:Class) REQUIRE c.qualifiedName IS UNIQUE;
CREATE CONSTRAINT package_name IF NOT EXISTS
  FOR (p:Package) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT graph_ingest_state_key IF NOT EXISTS
  FOR (s:GraphIngestState) REQUIRE s.key IS UNIQUE;
CREATE CONSTRAINT anchor_id IF NOT EXISTS
  FOR (a:Anchor) REQUIRE a.anchorId IS UNIQUE;
CREATE CONSTRAINT eventbus_address_value IF NOT EXISTS
  FOR (addr:EventBusAddress) REQUIRE addr.value IS UNIQUE;
CREATE CONSTRAINT eventbus_address_constant_key IF NOT EXISTS
  FOR (c:EventBusAddressConstant) REQUIRE c.key IS UNIQUE;
CREATE CONSTRAINT graph_ingest_metric_key IF NOT EXISTS
  FOR (m:GraphIngestMetric) REQUIRE m.metricKey IS UNIQUE;
CREATE INDEX class_name_idx IF NOT EXISTS FOR (c:Class) ON (c.name);
CREATE INDEX class_top_package_idx IF NOT EXISTS FOR (c:Class) ON (c.topPackage);
CREATE INDEX anchor_category_idx IF NOT EXISTS FOR (a:Anchor) ON (a.category);
CREATE INDEX metric_type_name_idx IF NOT EXISTS FOR (m:GraphIngestMetric) ON (m.metricType, m.metricName);
CREATE FULLTEXT INDEX class_fulltext IF NOT EXISTS
  FOR (c:Class) ON EACH [c.name, c.qualifiedName, c.package];

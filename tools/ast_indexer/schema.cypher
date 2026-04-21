CREATE CONSTRAINT class_qualified_name IF NOT EXISTS
  FOR (c:Class) REQUIRE c.qualifiedName IS UNIQUE;
CREATE CONSTRAINT package_name IF NOT EXISTS
  FOR (p:Package) REQUIRE p.name IS UNIQUE;
CREATE INDEX class_name_idx IF NOT EXISTS FOR (c:Class) ON (c.name);
CREATE INDEX class_top_package_idx IF NOT EXISTS FOR (c:Class) ON (c.topPackage);
CREATE FULLTEXT INDEX class_fulltext IF NOT EXISTS
  FOR (c:Class) ON EACH [c.name, c.qualifiedName, c.package];

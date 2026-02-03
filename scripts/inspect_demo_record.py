import json

# Construct the data programmatically to avoid massive string literal issues
message_system = {
    "role": "system",
    "content": "You are a senior Motadata engineer. Given a file and a task description,\ngenerate the precise unified diff to implement the change.\nAlways use proper unified diff format with --- a/, +++ b/, and @@ headers."
}

# Reconstructing the Java Content line by line to be safe
java_content_lines = [
    "/*",
    " * Copyright (c) Motadata 2024. All rights reserved.",
    " */",
    "",
    "package com.mindarray.datastore;",
    "",
    "import com.mindarray.Bootstrap;",
    "import com.mindarray.GlobalConstants;",
    "import java.util.concurrent.atomic.AtomicLong;",
    "",
    "public class Datastore",
    "{",
    "    private static final Logger LOGGER = new Logger(Datastore.class, GlobalConstants.MOTADATA_EVENT_BUS, \"Datastore\");",
    "    // ... (Snippet Truncated for Brevity in Demo) ...",
    "    protected void remove(long eventFile)",
    "    {",
    "        try",
    "        {",
    "             Files.deleteIfExists(Paths.get(path + GlobalConstants.PATH_SEPARATOR + eventFile + \".dat\"));",
    "        }",
    "        catch (Exception exception)",
    "        {",
    "            LOGGER.error(exception);",
    "        }",
    "    }",
    "}"
]
java_full = "File: motadata/src/main/java/com/mindarray/datastore/Datastore.java\n\nContent:\n```\n" + "\n".join(java_content_lines) + "\n```\n\nTask: refactoring\n\nGenerate the unified diff to implement this change."

# Reconstructing Diff
diff_lines = [
    "```diff",
    "index 2422b1f40d..2bc72aed42 100644",
    "--- a/motadata/src/main/java/com/mindarray/datastore/Datastore.java",
    "+++ b/motadata/src/main/java/com/mindarray/datastore/Datastore.java",
    "@@ -132,7 +132,10 @@ public class Datastore",
    "",
    "                         Files.deleteIfExists(Paths.get(path + GlobalConstants.PATH_SEPARATOR + entry.getKey() + \".dat\"));",
    "",
    "-                        LOGGER.trace(String.format(\"%s file deleted due to file pointer reached EOF\", entry.getKey()));",
    "+                        if(CommonUtil.traceEnabled())",
    "+                        {",
    "+                            LOGGER.trace(String.format(\"%s file deleted due to file pointer reached EOF\", entry.getKey()));",
    "+                        }",
    "",
    "                         iterator.remove();",
    "                     }",
    "```"
]
diff_full = "\n".join(diff_lines)

data = {
    "messages": [
        message_system,
        {"role": "user", "content": java_full},
        {"role": "assistant", "content": diff_full}
    ],
    "metadata": {
        "repo": "motadata", 
        "branch": "Delhi_University", 
        "file": "motadata/src/main/java/com/mindarray/datastore/Datastore.java"
    }
}

print("="*60)
print(f"IDENTITY: Gold Standard Training Record")
print(f"Repo: {data['metadata']['repo']} | File: {data['metadata']['file']}")
print("="*60)

for msg in data['messages']:
    print(f"\n[{msg['role'].upper()}]")
    print("-" * 20)
    print(msg['content'])
    print("-" * 20)

package agt.demo.rdf

denied_tools = {"delete_file", "execute_code", "shell", "rm_rf", "send_email", "ssh_connect", "write_system_file", "drop_table"}
allowed_tools = {"generate_rdf_kg", "validate_rdf", "create_rdf_infographic", "critique_rdf", "list_artifacts", "read_artifact", "compliance_verdict", "web_search", "summarize"}

tool_name = input.tool.name { input.tool.name != null }
default tool_name = ""

clearance_denied { input.tool.clearance == "denied" }
injection { re_match("(?i)(ignore|disregard|forget)[[:space:]]+(all[[:space:]]+)?(previous|prior|above)[[:space:]]+(instructions?|prompts?|rules?)", sprintf("%v", [input.policy_target.value])) }

result = {"decision": "deny", "reason": "tool_denied"} { denied_tools[tool_name] }
result = {"decision": "deny", "reason": "clearance_denied"} { clearance_denied }
result = {"decision": "deny", "reason": "prompt_injection"} { injection }
result = {"decision": "allow", "reason": "tool_allowed"} { allowed_tools[tool_name] }
result = {"decision": "allow", "reason": "default_allow"} { not denied_tools[tool_name]; not clearance_denied; not injection }

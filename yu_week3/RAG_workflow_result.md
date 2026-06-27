# 1 without rag using AI Chat Completion
Kestra 1.1 introduced several exciting features, significantly enhancing its capabilities and user experience. Here are 5 major features released in Kestra 1.1: 1. **Declarative UI Forms for Plugins:** This was a groundbreaking feature that allowed plugin developers to define their plugin's input fields (tasks, triggers, etc.) using a declarative YAML syntax directly within the plugin's blueprint. * **Brief Description:** Instead of relying solely on JSON Schema for UI generation, plugin creators could now specify the type of UI control (e.g., text input, dropdown, file upload, code editor), labels, descriptions, and other presentation aspects directly in the plugin definition. This led to much more user-friendly and tailored forms in the Kestra UI, improving discoverability and ease of use for complex plugin configurations. 2. **Secret Manager Integration:** Kestra 1.1 added robust integration with external secret management systems. * **Brief Description:** This feature allowed users to securely store and retrieve sensitive information (like API keys, database credentials) from dedicated secret managers such as HashiCorp Vault, AWS Secrets Manager, or Google Secret Manager. Instead of hardcoding secrets or relying on environment variables, Kestra could now dynamically fetch secrets at runtime, significantly enhancing security and compliance for production workloads. 3. **Namespace-Level Variables:** This release introduced the ability to define variables at the namespace level. * **Brief Description:** Previously, variables were primarily defined at the flow level. With namespace-level variables, users could define common configurations, credentials, or parameters that would be inherited and accessible by all flows within a specific namespace. This promoted reusability, reduced duplication, and simplified management of shared configurations across multiple related flows. 4. **Flow Template Engine (Handlebars):** Kestra 1.1 integrated the Handlebars templating engine for more dynamic and flexible flow definitions. * **Brief Description:** This allowed users to create more abstract and reusable flow templates where parts of the flow definition could be dynamically injected or configured based on variables or parameters. This was particularly useful for generating repetitive tasks, conditional logic, or adapting a generic flow to specific use cases without creating entirely new flow files, leading to more maintainable and modular flow designs. 5. **Audit Logs:** Kestra 1.1 introduced comprehensive audit logging capabilities. * **Brief Description:** This feature provided a detailed record of user actions and system events within Kestra, such as flow deployments, execution triggers, user logins, and configuration changes. 


# With RAG

✅ RAG Response (with retrieved context):
Kestra 1.1 introduced several major features. Here are at least 5 of them:
1. **New Filters**: The UI filters across Kestra were completely redesigned based on user feedback. The new design is cleaner, more intuitive, and more powerful, offering explicit filter options, single-click resets, saved filter combinations, and the ability to hide, show, or reorder table columns.
2. **No-Code Dashboard Editor**: This feature extends the No-Code Multi-Panel Editor to custom dashboards, allowing users to build and customize dashboards directly from the UI without writing YAML. Users can create data sources, visualizations, and charts using form-based tabs and switch between "Dashboard Code" and "No-Code" panels to see generated YAML in real-time.
3. **Multi-Agent AI Systems**: AI agents in Kestra can now use other AI agents as tools. This enables sophisticated multi-agent orchestration workflows where a primary agent can delegate subtasks to specialized expert agents, creating hierarchies of AI reasoning.
4. **Fix with AI**: When task runs fail, Kestra 1.1 can now provide AI-powered suggestions to help users quickly diagnose and resolve issues. This feature analyzes failed task runs and offers intelligent recommendations for fixing the problem.
5. **Human Task**: Available for Enterprise Edition users, this feature allows manual approval steps in workflows. When an execution reaches a human task, it pauses until designated users or group members approve and resume it, enabling human-in-the-loop workflows for critical operations.
🎉 Note that this response is detailed, accurate, and grounded in the actual release documentation. Compare this with the output from 1_chat_without_rag.yaml!


# 3 with websearch Tavily
The latest Kestra release is v1.3.25 (published 2026-06-25). Note: the Docker "latest" tag is a rolling tag that points to the most recent stable release (not an LTS); support ends when the next stable release is published (≈2 months).


# Question 3 > short answer output token
88 

# Question 4 > long answer output token
192 so its 2-4 times more

# QUestion 5 > 3 sentences output token
we edit the workflow file, replace 1 with 3 and compare the results
medium 1 sentence > 119
medium 3 sentences > 125
so its basically the same

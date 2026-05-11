# Commands

A visual overview of the `second_brain` CLI surface: subcommands, their
options, the filesystem store they read or write, and the environment
variables that configure them.

```mermaid
flowchart TD
    CLI["$ second_brain"]:::entry

    CLI --> TUI["(no subcommand)<br/>Launch interactive TUI"]:::cmd
    CLI --> NEW["new TITLE<br/>Create a new note"]:::cmd
    CLI --> LIST["list<br/>List all notes"]:::cmd
    CLI --> SHOW["show NUMBER<br/>Print note contents"]:::cmd

    NEW --> NEW_C["-c / --content TEXT<br/><i>inline body</i>"]:::opt
    NEW --> NEW_F["--from-file PATH<br/><i>body from file</i>"]:::opt
    NEW --> NEW_T["-t / --tag TAG<br/><i>repeatable; YAML frontmatter</i>"]:::opt
    NEW -. writes .-> FS[("SECOND_BRAIN_DIR<br/>~/second_brain")]:::store
    LIST -. reads .-> FS
    SHOW -. reads .-> FS
    TUI  -. reads/writes .-> FS

    subgraph ENV["Environment"]
      direction LR
      E1["SECOND_BRAIN_DIR"]
      E2["LOG_LEVEL"]
      E3["LOG_FILE"]
    end
    CLI -.-> ENV

    classDef entry fill:#1f2937,stroke:#facc15,color:#facc15,stroke-width:2px;
    classDef cmd   fill:#0f766e,stroke:#5eead4,color:#ecfeff;
    classDef opt   fill:#374151,stroke:#9ca3af,color:#f9fafb;
    classDef store fill:#7c2d12,stroke:#fdba74,color:#fff7ed;
```

The source of the diagram is also available as a standalone Mermaid file
at [`commands.mmd`](commands.mmd) for editing in Mermaid tools.

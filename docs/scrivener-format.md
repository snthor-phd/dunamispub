# Scrivener project format notes

Field notes on Scrivener 3's `.scriv` package, gathered by inspection on 3.5.2
(project format version 23). The format is undocumented, so treat everything here
as observed behavior rather than a specification.

## Package layout

```
Project.scriv/
├── Project.scrivx          the entire binder, as XML
├── Files/
│   ├── Data/
│   │   └── <UUID>/
│   │       ├── content.rtf     document body
│   │       ├── synopsis.txt    index-card text
│   │       └── notes.rtf       document notes
│   ├── version.txt         format version — "23" on 3.5.2
│   ├── user.lock           present only while the project is open
│   ├── binder.backup       Scrivener's own safety copy
│   ├── search.indexes      rebuilt automatically
│   └── styles.xml
├── Settings/
└── QuickLook/
```

**The binder hierarchy exists only in the XML.** `Files/Data/` is a flat pile of
UUID-named directories with no folder structure of its own. There is no directory
on disk corresponding to a binder folder, so you cannot add a document to a project
by dropping a file into the package — Scrivener would never see it.

## Binder item types

Observed values of the `Type` attribute:

| Type | Meaning |
|---|---|
| `DraftFolder` | The manuscript root. Exactly one per project. |
| `ResearchFolder` | The research root. Exactly one. |
| `TrashFolder` | Trash. Exactly one. |
| `Folder` | An ordinary folder |
| `Text` | A document |

A project needs all three singleton roots to open cleanly.

## Labels and statuses

Defined once at project level in `<LabelSettings>` and `<StatusSettings>`, and
referenced per item inside `<MetaData>` as `<LabelID>` and `<StatusID>`. IDs are
zero-based; `-1` means none.

Colors are floating-point RGB triples in an attribute: `Color="0.70 0.89 0.97"`.

**Confirmed by round-trip:** a hand-written project with `<LabelID>` and `<StatusID>`
set was opened in Scrivener 3.5.2, which rewrote the `.scrivx` and preserved both
elements. Scrivener discards metadata it doesn't recognize, so surviving a rewrite
is good evidence the element names are right.

## Writing to a project safely

The watcher never writes. The reconciler does, under four conditions, all required:

1. `Files/user.lock` is absent — the project is closed
2. `Files/version.txt` matches the version the tool was built against
3. A timestamped copy of the `.scrivx` is taken first
4. The project is verified to open afterward, or the backup is restored

The lock file is the important one. Writing to a `.scrivx` while Scrivener has the
project open means Scrivener will overwrite your change on its next autosave, or
worse, save a binder that disagrees with what is on disk.

## What breaks across versions

Point releases have not changed this structure in the 3.x line. A major version
would likely change the format and prompt for project conversion.

Because reads are tolerant — look up folders by title, ignore unknown attributes —
a format change degrades to "finds nothing" rather than to damage. The startup
canary exists so that silence gets reported instead of ignored.

# CakeML Build Tools

This is a tool I created to help build CakeML projects.
In particular, I plan to make this compatible with [EasyBakeCakeML](https://github.com/Durbatuluk1701/EasyBakeCakeML) so that you can have Rocq/Coq code extracted to "dependency-annotated" `.cml` files, and then use this tool to further progress your build process.

Make sure to review [quirks](#quirks) for some oddities about the tool that you might trip up on.

### The Overall Idea

CakeML does not have module/library/file imports, which can be rather painful when dealing with a large project.

My solution to this add a sort of "meta" import language that fits into CakeML comments. The standard is basically as follows:

Each .cml file that depends on another file will have its **first** line annotated with a comment

```sml
(* deps: <dependencies>+ *)
```

Some special processing is done for `dependencies`:

- If you depend on a file `X.cml` you just have to denote it with `X` and do not need to include the file extension
- You can specify dependencies nested in a folder via either `Y/X` or `Y.X`, these are considered equivalent by the resolver.
- Any dependency that does not start with `@` will be presumed to be relatively sourced, while `@` will be 'project-root' sourced.

  For example:

  - If you have dependency `X` in file `Y/Z.cml`, it is assumed that the dependency is at `Y/X.cml`.
  - This is compared to a dependency `@X` in `Y/Z.cml`, it is assumed that the dependency is `X.cml`

## Modes

There are a couple different options for how to use this tool. They are primarly controlled by the `--mode` argument

### `--mode print`

In print mode, all we do is resolve the dependencies and print them out. The default is to print them to the command line, but you can also print them to a file via the `--out <file>` command

### `--mode merge`

In merge mode, we resolve the dependencies, then merge them into one monolithic CakeML file (specified by `--out <file>`)

### `-mode build`

In build mode, we first create the monolithic CakeML file, then actually run it through the CakeML compiler `cake`, and finally through a C compiler to create an executable.

## Quirks

This is not an exceptionally well thought out or advanced tool. Their are currently some quirks about how it operates and simplifying assumptions are made.
If you have options you wish would be added, feel free to PR

#### Quirks:

1. Make sure you read [the overall idea](#the-overall-idea) and [modes](#modes) to understand how the processing is really done
1. We assume that your C compiler is `gcc`, the basis file is `basis_ffi.c` (and that it is available in the directory the tool is run in) and that the C compiler flags are `-O2 -lm`
1. Their is no cleaning capabilities yet, sorry
1. The `--out` argument is for the file you want the **monolithic CakeML file** to be in, we force the executable name in `build` mode to be the `out` file name - its extension

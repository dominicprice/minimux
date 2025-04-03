# minimux

A lightweight non-interactive terminal multiplexer.

## What is minimux?

Minimux allows you to run multiple programs in a single terminal
window. If this is useful for you, you probably already know it, but here are some reasons why it might be useful anyway:

* You are developing a program which requires running several
  different binaries at the same time, and you want to be able to
  start them all and read their logs in the same terminal window
* You have several background tasks you need to check occassionally
  and want one self-contained place to read them

Here are some things minimux is not:

* A replacement for tmux --- anything you can do with minimux you
  could definitely do better with tmux, but it could take more work
  and minimux might have some things included (such as colorizing
  output) which you'd have to hand roll with tmux
* A way to run interactive programs: minimux is dumb and doesn't send
  input to any of the programs it displays
  
Here is what it might look like if you were running a website with an
API and database:

```
                          My App Development Server
───────────────────────────────────────┬──────────────────────────────────────
                Frontend               │                 API
info: GET /index.html 200              │Starting the api
info: GET /index.html 200              │INFO: started
error: GET /doesnotexit.html 404       │WARN: this is a development api
                                       │
                                       │
                                       │
                                       │
                                       │
                                       ├──────────────────────────────────────
                                       │               Database
                                       │info: running database migrations
                                       │info: no migrations to run
                                       │
                                       │
```


## Installation

Install using the python package manager of your choice, if you have
`pipx` on your system then simply `pipx install minimux`

## Usage

Simply run `minimux CONFIG_FILE`; the configuration file is described
in the next section

## The Configuration File

The configuration file is described here in two ways
1. For new users, a small example on how to build up a configuration
   from scratch
2. For existing users who need to look something up, a reference of
   all the available sections and options

### Guided tutorial

In the `example` directory of this repo you'll find a variety of `.ini`
config files and three subdirectories `api`, `database` and
`frontend`. Each directory contains a makefile with the single target
`dev` which spit out some totally legit looking log messages when run.

You can run the example configs now by `cd`ing into that directory and
running `minimux CONFIG_FILE`. In this tutorial we will start with a
blank config file and work our way up to the `tutorial.ini` config.

The problem we are trying to solve is this: to test our app locally we
need to run the frontend, api and database at the same time. We want
to do this all with one simple command, and to be able to inspect the
logs of all three programs in real time.

Let us start with a blank `app.ini`. The simplest way to solve the problem above is to write a config as follows:

```
[main]
panels = frontend,api,database

[frontend]
command = make -C frontend dev

[api]
command = make -C api dev

[database]
command = make -C database dev
```

Now when we run `minimux app.ini` we will see all three programs run
side by side.

The `main` section is the entrypoint for minimux, and the `panels`
options holds a list of the section names which describe what to
display. In our simple case, each section just holds a `command`
option with a command to run.

It might be nice to add headings to each section so we know what
program it is showing the output of. We can do this by adding a
`title` option to each section, for example:

```
[api]
title = API
command = make -C api dev
```

Now the title is displayed at the top of the program's output. We can
also specify a title in the `main` section, which will be displayed at
the top of the entire window:

```
[main]
title = My App Development Server
panels = frontend,api,database
```

Now suppose that frontend outputs far more than the other two
programs, and we wish to dedicate more space to it. We can start by
adding a `weight` option to it, which will alter the ratio of how the
space is divided:

```
[frontend]
command = make -C frontend dev
weight = 2
```

Now the frontend will be twice as large as the other two
sections. This makes the other two rather squeezed in though, so maybe
it would be better to have them on top of each other rather than
sharing the space side by side. To do this, we can create a new
section, let's say `backend`, which instead of being command is a
definition of a subpanel:

```
[backend]
vertical = true
panels = api,database
```

The `vertical` option ensures that the two subpanels are stacked
vertically instead of horizontally. In the main section we now
reference the `rhs` section:

```
[main]
panels = frontend,backend
```

And we get the frontend on the left hand side of the terminal, and the
two other programs on top of each other on the right hand side.

As our programs are producing (totally real) logs, we might want to
colorize the output depending on what is being output, for instance
showing errors in red. To do this we can add rules to the
commands. First, we add a new section:

```
[rule.warn]
literal = warn
ignorecase = true
fg = yellow
```

The name of the section `rule.warn` is totally arbitrary, here I have
just started its name with `rule.` to make it clear that it is
defining a rule, but we could just have validly named it `warn`.

The `literal` option specifies a literal string which we want to match
for the rule to apply. `ignorecase` specifies that the match should be
case insensitive, and `fg` specifies the foreground color we want
lines we match to have. As well as `fg` there are some other
attributes which we can set, see the `Attr` type in the reference at
the bottom of the readme for a list of them.

To register the rules with one of our commands, we reference it in the
`rules` option:

```
[api]
title = API
command = make -C api dev
rules = rule.warn
```

Now when we run minimux, we should see any log lines from the api
with the word `warn` in them are displayed in yellow.

There may be a set of common rules we wish to apply to all commands. Lets also add a rule for highlighting errors, which we define as any lines with the word `error` or `fatal` in them:

```
[rule.error]
regex = error|fatal
ignorecase = true
fg = rgb(200, 0, 0)
```

Instead of a literal rule, we have used a regex instead for the error
message as there are multiple alternatives we wish to match. We have
also specified the colour as an rgb value instead of a name.

To make these rules apply to all commands by default, we add them to a special section:

```
[default]
rules = rules.warn,rules.error
```

Now any command which doesn't explicitly set the `rules` option will
default to applying both `rules.warn` and `rules.error`. In fact, any
option you specify in the `default` section will work like this, but
it is most useful for specifying rules.

We might also want to make some of the commands stand out by changing their background colour. To do this we can add the `bg` option to a command or panel. Let's make the frontend have a blue background and the backend have a green background:

```
[frontend]
command = make -C frontend dev
weight = 2
bg = #000088

[backend]
vertical = true
panels = api,database
bg = green
```

Now when we run minimux we can see the background effects applied to
the two sides of the window.

Any attributes which are applied to an element are are inherited by
any children of that element, so although we applied the green
background colour to the backend panel, bot the api and database
commands inherited it. Similarly, the warn and error rules inherited
the green background colour too.

Finally, there are two other special sections, `title` and `seperator`
which we can also add attributes to. The `title` section will theme
the main title at the top of the window, and the `seperator` section
the seperator lines between sections. If instead of lines, we just
wanted black boxes to separate the commands we could write

```
[seperator]
fg = black
bg = black
```

and to make the title bold we can write

```
[title]
bold = on
```

And there we go - that covers pretty much everything minimux can be
configured to do!

### Complete reference

#### Well-known sections

These sections are known by the config parser and will be handled in a
special manner
* `[main]: Panel` The entrypoint of the config which defines how the
  top level window will be split up
* `[seperator]: Attr` Defines how separators are displayed
* `[title]: Attr` Defines how the main window title is displayed

#### Section types

This shows the complete list of options available to different section
types. Options ending with an ellipse denote that all the options for
another section type are permitted.

Options which are marked with an asterisk are required for that section.

* `Attr` Customise how output is displayed
  * `fg: string` The foreground colour, see 'Colours' for allowed values. 
  * `bg: string` The background colour, see 'Colours' for allowed values
  * `blink: bool` Add a blinking effect
  * `bold: bool` Display in bold face
  * `dim: bool` Display dimmed
  * `reverse: bool` Invert the foreground and background colours
  * `standout: bool` Add a standout effect
  * `underline: bool` Display with an underline
* `Element` A window in the output
  * `weight: int` The number of divisions of space the element should take up
  * `attrs...: Attr` Attributes to apply to the element
* `Command` A command to tail the output of
  * `title: string` A title to be displayed above the output of the command
  * `command: string`* The command to run
  * `rules: list` A comma separated list of the section names denoting
    rules to apply
  * `title_attr: string` Name of the section defining the attributes of the title
  * `padding: int | int,int | int,int,int,int` Padding around command output. Either one value for all sides, x value followed by y value or top, right, bottom and left values
  * `element...: Element` Element options
* `Panel` A 1D arrangement of elements
  * `vertical: bool` If true, subpanels are stacked vertically
  * `panels: list`* A comma separated list of section names denoting
    the subpanels to display
  * `element...: Element` Element options 
* `LiteralRule` A rule based on substring matching
  * `literal: string`* The substring to match
  * `ignorecase: bool` If true then the matching is performed case-insensitive
  * `attrs...: Attr` Attributes to apply to the matched lines
* `RegexRule` A rule based on regex matching
  * `regex: string`* The regex to match
  * `ascii: bool` If true then character classes only match ascii characters
  * `ignorecase: bool` If true then the matching is performed case-insensitive
  * `multiline: bool` If true then the `^` symbol also matches linebreaks
  * `dotall: bool` If true then the `.` symbol also matches newlines
  * `verbose: bool` Allows writing verbose regexes
  * `attrs...: Attr` Attributes to apply to the matched lines

#### Colours

Colours can be defined in any of the following ways:
* Using a builtin colour name: `black`, `blue`, `cyan`, `green`,
  `magenta`, `red`, `white` or `yellow`
* Using a hex code, e.g. `#fa346f`
* Using an rgb code, e.g. `rgb(100, 23, 46)`

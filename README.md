# kattis-tools

Tools for running, judging and submitting files for the Kattis system

## Features

- Creating directories for problems and downloading their samples automatically
- Compiling and running code with a sample as input
- Judging solutions based on the sample test data
- Uploading submissions

## Installation

1. Download/clone this repository
2. Install Python (kattis-tools supports both Python 2 & 3)
3. Install dependencies by running `python -m pip install -r requirements.txt`

kattis-tools is a python script. Run it with `python kattis-tools.py`

## Usage

To start working on a new project, run `python kattis-tools.py start <URL>` with the URL of the problem. As an example, I will be solving [this problem](https://open.kattis.com/problems/simpleaddition).

```
$ python kattis-tools.py start https://open.kattis.com/problems/simpleaddition
```

This creates the following problem directory and downloads all samples into it:

```
simpleaddition/
├── 1.ans
├── 1.in
├── 2.ans
├── 2.in
└── problem.json
```

Your solution code file should be located in that directory. Its name does not matter. When debugging your code, you can run `python kattis-tools.py run <sample>` to run your code with a specific sample input. (Since this is the first time we are running kattis-tools, we need to specify our language with `-l`. kattis-tools will remember this for the future)

```
$ python kattis-tools.py run 1 -l py
running...
1379
took 0.053s
```

If you want to test your solution with all test cases, run `python kattis-tools.py judge`:

```
$ python kattis-tools.py judge
Found 2 tests

testing with "1.in"...
Accepted
took 0.050s

testing with "2.in"...
Wrong Answer
got
12345
instead of
10000000000000

took 0.049s

1/2 passed
worst time: 0.050s
```

If you want to submit your solution you should run `python kattis-tools.py submit`. Once your solution has been submitted kattis-tools will open the submission in your web browser.

```
$ python kattis-tools.py submit
Before you can submit problems you need to register the token specific to this Kattis subdomain with kattis-tools. Your browser will open to the correct page.
Press Enter to continue...
From the webpage, Please copy paste the two lines with "username" and "token" here and press enter a few times:
username: *************
token: ****************************************************************

Submission received. Submission ID: 3544950.
```

## Configuration

Configuration files exist in the `config-kattis-tools` folder.

config.json:

```json5
{
    "last_language": "py", // The short name of the last used language (and the default language to use). Can be modified with the -l command line argument
    "last_problem": "hello" // The id of the last run problem (and the default problem to run). Can be modified with the -p command line argument
}
```

By default, kattis-tools comes configured with only 2 languages, Python 2 and C++. If you use a different language you will have to create a new json file in the `config-kattis-tools/languages` folder. Feel free to submit a pull request with it so it can be added to kattis-tools. Here is an example file for C++ on windows:

```json5
{
    "name": "C++", // The Kattis name of the language. Must be one of the names in the codeblock below this one, otherwise Kattis will return "Invalid Language" when submitting.
    "extensions": [".cpp", ".c++", ".cc", ".cxx", ".h"], // File extensions for this language
    "short_names": ["cpp", "c++", "cxx"], // Short names for this language, they are what identifies the language when running -l.
    "before_run": "cd ${problemDir} && g++ -static ${fileName} -o ${fileNameNoExtension}.exe", // A command to run before running your program. Usually used for the compile command, can be left empty if your language does not require compilation. Only runs once before all tests when judging.
    "run_command": "${filePathNoExtension}.exe" // The command that runs your program.
}
```

valid Kattis language names:

```
C
C#
C++
Go
Haskell
Java
JavaScript (Node.js)
JavaScript (SpiderMonkey)
Kotlin
Objective-C
Pascal
PHP
Prolog
Python 2
Python 3
Ruby
Rust
Scala
```

You may have noticed variables in the language config. Here is a full list of them:

```
${filePath}
${fileName}
${fileNameNoExtension}
${problemDir}
${workingDir}
```

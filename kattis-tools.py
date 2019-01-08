import argparse
import json
import sys
import os
import time
import re
import requests
import io
import zipfile
import webbrowser as wb
from subprocess import Popen, PIPE

if sys.version_info[0] < 3:
    FileNotFoundError = IOError
    json.decoder.JSONDecodeError = ValueError
    input = raw_input

KATTIS_MODES = ["run", "judge", "submit", "start"]
CONFIG_FOLDER = "config-kattis-tools"

def load_config():
    global config
    try:
        with open("%s/config.json" % CONFIG_FOLDER) as f:
            config = json.load(f)

        config["languages"] = {}
        for language in os.listdir("%s/languages" % CONFIG_FOLDER):
            if not language.endswith(".json"): continue

            with open("%s/languages/%s" % (CONFIG_FOLDER, language)) as f:
                data = json.load(f)
            config["languages"][data["name"]] = data

    except (json.decoder.JSONDecodeError, FileNotFoundError):
        print("One of the configuration files is corrupted or missing. Fix it or download a new template from github.")
        exit(1)

def update_config():
    with open("%s/config.json" % CONFIG_FOLDER, "w") as f:
        json.dump({key:value for key, value in config.items() if key != "languages"}, f, indent=4, sort_keys=True)

def strip_whitespace(string):
    """strips all whitespace at beginning and end of string"""
    string = re.sub(r"^\s*", "", string)
    string = re.sub(r"\s*$", "", string)
    return string

def find_problem_file():
    """finds the problem file in the problem directory"""
    files = os.listdir("%s" % args.problem_id)
    for file in files:
        for extension in config["languages"][language]["extensions"]:
            if file.endswith(extension):
                return file
    print("A code file written in {lang} could not be found in the {problem} folder. Make sure your {lang} solution code file is in that folder. If you are not developing in {lang}, run kattis-tools with -l to choose your language.".format(problem=args.problem_id, lang=config["languages"][language]["name"]))
    exit(1)

def parse_variables(string):
    """parses command variables"""
    replace = {
        "${filePath}": os.path.join(os.getcwd(), args.problem_id, problem_file),
        "${filePathNoExtension}": os.path.join(os.getcwd(), args.problem_id, problem_file.rsplit(".", 1)[0]),
        "${fileName}": problem_file,
        "${fileNameNoExtension}": problem_file.rsplit(".", 1)[0],
        "${problemDir}": os.path.join(os.getcwd(), args.problem_id),
        "${workingDir}": os.getcwd(),
    }

    for variable, value in replace.items():
        string = string.replace(variable, value)

    return string

def before_run_problem():
    """runs the before_run_problem command"""
    before_run = parse_variables(config["languages"][language]["before_run"])
    if before_run != "":
        print("Running before_run...")
        p = Popen(before_run, shell=True)
        code = p.wait()
        if code != 0:
            print("before_run exited with error code %s" % (int(code)))
            exit()

def run_problem(sample, directStdio=False):
    """runs the problem once and return time with stdout"""
    start = time.time()
    if directStdio:
        p = Popen(parse_variables(config["languages"][language]["run_command"]), stdin=open("%s/%s" % (args.problem_id, sample)), stdout=sys.stdout, stderr=sys.stderr, shell=True)
    else:
        p = Popen(parse_variables(config["languages"][language]["run_command"]), stdin=open("%s/%s" % (args.problem_id, sample)), stdout=PIPE, stderr=PIPE, shell=True)
    code = p.wait()
    end = time.time()

    stdout, stderr = p.communicate()
    if not directStdio:
        out = stdout.decode().replace("\r","") # get stdout
        out = strip_whitespace(out)
        return end-start, out, code, stderr
    return end-start, None, code, None

load_config()

parser = argparse.ArgumentParser(description="Tools for running, judging and submitting files for the Kattis system")

parser.add_argument(
    "mode",
    metavar="mode",
    type=str,
    help="The function you want kattis-tools to perform. Choose between %s and %s."
    % (", ".join(KATTIS_MODES[:-1]), KATTIS_MODES[-1]),
    choices=KATTIS_MODES,
)
parser.add_argument(
    "arg2",
    metavar="arg2",
    type=str,
    nargs="?",
    help='When using "kattis-tools run", this is the name of the input file to feed to stdin. It should be in the problem folder and have the extenstion ".in". When using "kattis-tools start" this is the url to the problem on the kattis website.',
)
parser.add_argument(
    "-l",
    "--language",
    default=config["last_language"],
    type=str,
    help='The short name of the language kattis-tools should run the problem in. This can be found in one of the language configs in the %s/languages folder and additional languages can be configured there as well. If left out, the last used language is used. Example: "py" for python' % CONFIG_FOLDER,
    choices=[short_name for language in config["languages"].values() for short_name in language["short_names"]],
)
parser.add_argument(
    "-p",
    "--problem-id",
    default=config["last_problem"],
    type=str,
    help="The id of the problem you want kattis-tools to manage. Can be found in the problem url or the folder name. If left out, the last used problem id is used.",
)

args = parser.parse_args()
language = [key for key, values in config["languages"].items() if args.language in values.get("short_names", [])][0]

if args.problem_id not in os.listdir(".") and args.mode != "start":
    print("The current problem id ({id}) is invalid. Make sure there is a folder with the same name as the problem id in the same folder as this script. If you are not working on {id}, run kattis-tools with the -p flag and specify your problems id.".format(id=args.problem_id))
    exit(1)

if args.mode != "start": problem_file = find_problem_file()

config["last_language"] = args.language
config["last_problem"] = args.problem_id
update_config()

if args.mode == "run":
    if not args.arg2:
        print("Please provide which .in file to feed to stdin as the last argument.")
        exit(1)
    if not os.path.isfile("%s/%s.in" % (args.problem_id, args.arg2)):
        print("File %s.in could not be found in the %s folder." % (args.arg2, args.problem_id))
        exit(1)
    
    before_run_problem()
    print("running...")
    out = run_problem("%s.in" % args.arg2, True)
    print("took %.3fs" % out[0])

if args.mode == "judge":
    files = os.listdir("%s" % args.problem_id)
    samples = []
    for file in files:
        if file.endswith(".in") and "%s.ans" % file.split(".")[0] in files:
            samples.append(file)
    
    if samples == []:
        print("No indata found with matching answers. make sure your indata has the extension .in and that its solution has the same name with extension .ans.")
        exit(1)
    
    print("Found %s tests" % len(samples))
    before_run_problem()

    correct = 0
    worst = 0

    for sample in samples:
        print('\ntesting with "%s"...' % sample)
        out = run_problem(sample)
        ans = open("%s/%s"%(args.problem_id, sample.replace(".in", ".ans"))).read()
        ans = strip_whitespace(ans)

        if out[2] != 0:
            print("Runtime Error, exit code %s" % out[2])
            print(out[1])
            print(out[3])
        elif out[1] == ans:
            correct += 1
            print("Accepted")
        else:
            print("Wrong Answer")
            print("got \n%s\ninstead of \n%s\n"%(out[1],ans))
        print("took %.3fs" % out[0])
        worst = max(worst, out[0])
    
    print("\n%s/%s passed"%(correct,len(samples)))
    print("worst time: %.3fs" % worst)
    if correct == len(samples):
        if input("Everything passed, do you want to submit? (Y/N) ").lower() == "y":
            args.mode = "submit"

if args.mode == "start":
    if not args.arg2:
        print("Please provide the kattis URL to the problem as the second argument.")
        exit(1)

    match = re.match(r"^.*\/(.*)\.kattis.com\/problems\/([^\/]*)\/?.*$", args.arg2)

    if not match:
        print("The URL you provided is incorrect. Make sure that it is the URL for the problem on kattis.com.")
        exit(1)
    
    subdomain = match.group(1)
    problem_id = match.group(2)
    config["last_problem"] = problem_id
    update_config()

    if problem_id in os.listdir("."):
        print("A problem enviroment for this problem already exists. The problem config has been updated.")
    else:
        os.mkdir(problem_id)

    with open("%s/problem.json" % problem_id, "w") as f:
        f.write('{"subdomain": "%s"}' % subdomain)

    r = requests.get("https://%s.kattis.com/problems/%s/file/statement/samples.zip" % (subdomain, problem_id))

    if r.status_code != 200:
        print("Failed to download samples with status code %s." % r.status_code)
        exit(1)
    else:
        file = io.BytesIO()
        file.write(r.content)
        archive = zipfile.ZipFile(file)
        archive.extractall(problem_id)
    
    print("A problem enviroment for problem %s has been created." % problem_id)

if args.mode == "submit":
    if not os.path.isfile("%s/problem.json" % args.problem_id):
        print('This problem does not have a configuration file yet. Before submitting, please run kattis-tools in start mode with the kattis URL of the problem first like so:\n"kattis-tools.py start <kattis problem URL>"')
        exit(1)

    with open("%s/problem.json" % args.problem_id) as f:
        problem_config = json.load(f)

    try:
        with open("%s/credentials.json" % CONFIG_FOLDER) as f:
            credentials = json.load(f)
    except (IOError, json.decoder.JSONDecodeError):
        credentials = {}

    token = credentials.get(problem_config["subdomain"])
    
    if not token:
        input("Before you can submit problems you need to register the token specific to this kattis subdomain with kattis-tools. Your browser will open to the correct page. \nPress Enter to continue...")
        wb.open_new_tab("https://%s.kattis.com/download/kattisrc" % problem_config["subdomain"])
        print('From the webpage, Please copy paste the two lines with "username" and "token" here and press enter a few times:')
        username = ""
        token = ""
        for i in range(6):
            data = input()
            match = re.match("^username: (.*)$", data)
            if match:
                username = match.group(1)
                continue
            
            match = re.match("^token: (.*)$", data)
            if match:
                token = match.group(1)
                continue
            
            if username != "" and token != "":
                break
        else:
            print('Both username and token could not be found. Please make sure you copy paste the part with "username:" and "token:" and try again.')
            exit(1)

        credentials[problem_config["subdomain"]] = (username, token)
        with open("%s/credentials.json" % CONFIG_FOLDER, "w") as f:
            json.dump(credentials, f, indent=4, sort_keys=True)
    
    r = requests.post(
        "https://%s.kattis.com/login" % problem_config["subdomain"],
        data= {
            "user": credentials[problem_config["subdomain"]][0],
            "token": credentials[problem_config["subdomain"]][1],
            "script": "true",
        },
        headers={'User-Agent': 'modified kattis-cli-submit'}
    )
    
    if r.status_code != 200:
        if r.status_code == 403:
            print("The token is either incorrect, has expired or you have changed your password since registering it. Please execute the same command again to register a new token.")
            del credentials[problem_config["subdomain"]]
            update_config()
        else:
            print("Login failed with status code %s" % r.status_code)
        exit(1)
    
    data = {
        "submit": "true",
        "submit_ctr": 2,
        "language": config["languages"][language]["name"],
        "mainclass": "",
        "problem": args.problem_id,
        "tag": "",
        "script": "true",
    }

    path = "%s/%s" % (args.problem_id, problem_file)
    with open(path) as f:
        file = [(
            'sub_file[]',
            (
                os.path.basename(path),
                f.read(),
                'application/octet-stream'
            )
            )]
    
    r = requests.post(
        "https://%s.kattis.com/submit" % problem_config["subdomain"],
        data=data,
        files=file,
        cookies=r.cookies,
        headers={'User-Agent': 'modified kattis-cli-submit'},
    )

    if r.status_code != 200:
        print("Login failed with status code %s" % r.status_code)
        exit(1)
    
    result = r.content.decode('utf-8').replace('<br />', '\n')
    print(result)

    if "Submission ID:" in result:
        id = re.search(r"\d+", result).group(0)

        wb.open_new_tab("https://%s.kattis.com/submissions/%s" % (problem_config["subdomain"], id))
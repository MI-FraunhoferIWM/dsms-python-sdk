# DSMS-SDK Docs

If you find any error or problem with the documentation, please create an issue [in this repository](https://github.com/MI-FraunhoferIWM/dsms-python-sdk/issues).

## Local Rendering


### HTML
A server will start, generate the docs and listen for changes in the source files.
This can be done by using docker or installing the development environment directly on the you machine. Next are installation guides for Docker and Linux OS.

#### Docker
First, build the Docker image by running the following command:
```shell
$ docker build -f Dockerfile.docs -t dsms-sdk-docs .
```

Then, start the program by running:
```shell
$ docker run -it --rm -v $PWD:/app -p 8000:8000 dsms-sdk-docs
```

#### Linux
At an OS level (these commands work on Linux Debian):
```shell
$ sudo apt install pandoc graphviz default-jre
$ sudo apt-get install texlive-latex-recommended \
                       texlive-latex-extra \
                       texlive-fonts-recommended \
                       latexmk
```
The python dependencies:
```shell
$ pip install -e .[docs]
```

Now you can start the server and render the docs:
```
$ sphinx-autobuild docs/source docs/build/html
```
The documentation will be available on [`http://127.0.0.1:8000`](http://127.0.0.1:8000).

#### VSCode

To render the documentation using VSCode, follow these steps:

1. **Ensure Live Server Extension is Installed:**

    You need to have the Live Server extension installed in VSCode. If you don't have it installed, you can find it [here](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer).

2. **Build the Documentation:**

    Open your terminal in VSCode and run the following command to build the HTML documentation:

```shell
$ make html
```
3. **Open the Documentation with Live Server:**

    After building the documentation, navigate to the docs/build/html directory in VSCode.
    Right-click on the index.html file and select the option "Open with Live Server".

4. **Access the Documentation:**

    The documentation will open in your default web browser and be accessible at http://127.0.0.1:5500.

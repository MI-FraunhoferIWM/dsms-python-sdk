# DSMS Documentation

Welcome to documentation of DSMS!

Here you will find all the information about DSMS and installation, setup and basic usage of the associated python based DSMS-SDK.


````{panels}
:body: text-center.

---
**DSMS**

Introduction to DSMS

```{link-button} dsms.html
:text: About DSMS
:classes: btn-outline-primary stretched-link

---
**DSMS-SDK**

 Overview of the DSMS-SDK

```{link-button} dsms_sdk.html
:text: Basics of DSMS-SDK
:classes: btn-outline-primary stretched-link

---
**Tutorials**

Get Started with using DSMS-SDK.

```{link-button} dsms_sdk/tutorials/1_introduction.html
:text: Jump to the tutorials
:classes: btn-outline-primary stretched-link


````

Note that these docs are an ongoing effort, so they are likely to change and evolve.
Feel free to report any issues/missing information so we can take a look into it.

```{toctree}
:hidden: true
:caption: Introduction
:maxdepth: 4
:glob:

The Data Space Management System<dsms>
```


```{toctree}
:hidden: true
:caption: DSMS Python SDK
:maxdepth: 4
:glob:

dsms_sdk/dsms_sdk
dsms_sdk/dsms_config_schema
dsms_sdk/dsms_kitem_schema

```

```{toctree}
:hidden: true
:caption: Tutorials
:maxdepth: 4
:glob:

dsms_sdk/tutorials/*

```

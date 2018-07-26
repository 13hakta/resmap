# resmap - Android application resource usage analyzer

resmap analyzes decompiled [Android](https://www.android.com/) application (apk) with [apktool](https://ibotpeaches.github.io/Apktool/).
Supports multidex from 1.0.1

You may set options:
--cleanup [y/n] - clean definitions from unused types

--replace [y/n] - replace original files

--cache [y/n] - create cache with usage data

Clean from unused resources:
`resmap.py -c -r`

Be warned: attr/font type is not taken in account.

# java_orphan - Android application Java class usage analyzer

Must be ran in smali folder

It looks in manifest for main class and services.
Everything not linked with them is marked as unused.

# jvnav - Web JS application to navigate class usage dependency

Put file `usemap.txt` to js folder.

# resmap - Android application resource usage analyzer

resmap analyzes decompiled [Android](https://www.android.com/) application (apk) with [apktool](https://ibotpeaches.github.io/Apktool/).

You may set options:

cleanup [y/n] - clean definitions from unused types

replace [y/n] - replace original files

backup [y/n] - create backups of original files

Clean from unused resources:
`resmap.py -c -r`

Be warned: attr/font type is not taken in account.

# java_orphan - Android application Java class usage analyzer

Must be ran in smali folder

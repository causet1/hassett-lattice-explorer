-- SPDX-License-Identifier: MIT
path = prepend(currentFileDirectory, path);
args = drop(scriptCommandLine,1);
prefix = (if #args == 0 then currentDirectory() | "build/macaulay2-docs/"
    else args#0 | "/");
installPackage("HassettLattices", InstallPrefix=>prefix,
    RerunExamples=>true, CheckDocumentation=>true, IgnoreExampleErrors=>false);

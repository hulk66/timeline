#!/bin/bash
SRC=${1:-} 

if [ -z $SRC ] || [ ! -e "$SRC" ]; then
    echo "Source file '$SRC' does not exist"
    exit 1
fi

OUTPUT="// generated"

while IFS="" read -r line || [ -n "$line" ]; do
    use_line=$line

    if [[ $line =~ "window." ]]; then
        ENVIRONMENT_VARIABLE_NAME=`echo $line | sed -re 's/window\.(.*)\s+\=(.*);/\1/g'`
        value=${!ENVIRONMENT_VARIABLE_NAME}

        if [[ ${value} && ${value-x} ]]; then
            use_line="window.$ENVIRONMENT_VARIABLE_NAME = '$value';"
        fi
    fi

    OUTPUT="$OUTPUT\n$use_line"
done <$SRC

echo -en $"$OUTPUT"
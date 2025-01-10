#!zsh
for cat_dir in ../asterix-specs/specs/cat*
do
    echo $(basename $cat_dir)
    for spec_file in $cat_dir/cat*
    do
        echo "  $(basename $spec_file)"
        mkdir specs/$(basename $cat_dir) 2>/dev/null
#        aspecs convert -f $spec_file --ast --json > specs/$(basename $cat_dir)/$(basename -s .ast $spec_file).json
        aspecs convert --input-ast --output-json $spec_file > specs/$(basename $cat_dir)/$(basename -s .ast $spec_file).json
    done
done

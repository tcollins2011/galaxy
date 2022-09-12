#!/usr/bin/env bash

data=$1

function single_copy_filter () { 
    perl /EDTA/util/output_by_list.pl \
    1 \
    <(perl -nle 's/#.*//; print $\_' $1.mod.EDTA.TElib.novel.fa) \
    1 \ 
    <(perl /EDTA/util/find_flTE.pl $1.mod.out | \
    awk '{print $10}'| \
    sort| \
    uniq -c |\
    perl -nle 'my ($count, $id) = (split); if ($id=~/LTR/){next if $count<=2} else {next if $count ==1} print $_' |\
    awk '{print $2}') -FA > $1.mod.EDTA.TElib.novel.fa.real &
}

single_copy_filter $data

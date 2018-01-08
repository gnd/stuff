#!/bin/sh
# php-based shell search
# gnd, 2012 - 2018
#
# note:
# 	this basically searches all php files for "some patterns"
# 	which are abstracted from real-life occurences
# 	of course patterns might change and this list is by far not exhaustive
# 	but as a early warning system of sorts it pretty much works..
#
###############################################################################

# some globals
SCRIPT_DIR=""
SEARCH_DIR=""
MONITORING=""
MESSAGE=""
NOTIFY=0
IFS=$'\n'

# prep tmpfile
RND=`openssl rand -hex 2`
TMPFILE="/tmp/diff_"$RND
touch $TMPFILE
chmod 600 /tmp/diff_$RND

# prep compare
compare() {
	TXT=$1
	OLD=$2
	NEW=$3	
	OLDNUM=`wc -l < $SCRIPT_DIR/$OLD`
	NEWNUM=`wc -l < $SCRIPT_DIR/$NEW`
	if [ "$OLDNUM" -ne "$NEWNUM" ]; then
		NOTIFY=1
	        echo "$TXT - new: $NEWNUM old: $OLDNUM" > $TMPFILE
	        diff --suppress-common-lines $SCRIPT_DIR/$OLD $SCRIPT_DIR/$NEW >> $TMPFILE
	fi
}

# prep old cache
rm $SCRIPT_DIR/eval.txt
rm $SCRIPT_DIR/base.txt
rm $SCRIPT_DIR/hex.txt
mv $SCRIPT_DIR/eval_base.txt $SCRIPT_DIR/eval_base.old
mv $SCRIPT_DIR/eval_glob.txt $SCRIPT_DIR/eval_glob.old
mv $SCRIPT_DIR/base_cfun.txt $SCRIPT_DIR/base_cfun.old
mv $SCRIPT_DIR/hex_eval.txt $SCRIPT_DIR/hex_eval.old
mv $SCRIPT_DIR/eval_split.txt $SCRIPT_DIR/eval_split.old

# find out new occurences (eval_base & eval_glob)
find $SEARCH_DIR -type f -name "*.php" -exec grep -l "eval(" {} \; >> $SCRIPT_DIR/eval.txt
for k in `cat $SCRIPT_DIR/eval.txt`
do
        grep -l base64_decode "$k" >> $SCRIPT_DIR/eval_base.txt
	grep -l '$GLOBALS\[$GLOBALS' "$k" >> $SCRIPT_DIR/eval_glob.txt
done

# find out new occurences (base_cfun)
IFS=$'\n'
find $SEARCH_DIR -type f -name "*.php" -exec grep -l "base64_decode(" {} \; >> $SCRIPT_DIR/base.txt
for k in `cat $SCRIPT_DIR/base.txt`
do
        grep -l create_function "$k" >> $SCRIPT_DIR/base_cfun.txt
done

# find out new occurences (hex + eval)
find $SEARCH_DIR -type f -name "*.php" -exec grep -l '[\][x][0-9a-fA-F]\{2\}[\][x][0-9a-fA-F]\{2\}[\][x][0-9a-fA-F]\{2\}[\][x][0-9a-fA-F]\{2\}[\][x][0-9a-fA-F]\{2\}[\][x][0-9a-fA-F]\{2\}' {} \; >> $SCRIPT_DIR/hex.txt
for k in `cat $SCRIPT_DIR/hex.txt`
do
        $SCRIPT_DIR/decode_hex.py -l '${"GLOBALS"}' 'eval[^(]*\(' "$k" >> $SCRIPT_DIR/hex_eval.txt
done

# find out new occurences ( eval/* .* */( )
find $SEARCH_DIR -type f -name "*.php" -exec grep -l 'eval\/\*.*\*\/(' {} \; >> $SCRIPT_DIR/eval_split.txt

# search for occurence changes
compare "evals + base64" eval_base.old eval_base.txt
compare "evals + base64" eval_glob.old eval_glob.txt
compare "base64 + c-fun" base_cfun.old base_cfun.txt
compare "evals split" eval_split.old eval_split.txt
compare "hex + eval" hex_eval.old hex_eval.txt

# notify on any changes
if [ $NOTIFY -eq 1 ]; then
	cat $TMPFILE | mail -s $MESSAGE $MONITORING 
        rm $TMPFILE
fi
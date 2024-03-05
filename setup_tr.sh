#!/bin/sh
#
# bash scripts for create i18n   
#
domain=nnmbot
PATH_TR="./locales"
PATH_IN="."
RETVAL=0
 
case "$1" in
        extract)
                python setup.py extract_messages --output-file ${PATH_TR}/messages.pot --input-paths ${PATH_IN} --omit-header --no-wrap
                ;;
          init)
                #Init tarnslation tree
                python setup.py init_catalog -l en -i ${PATH_TR}/messages.pot -o ${PATH_TR}/en/LC_MESSAGES/${domain}.po
                python setup.py init_catalog -l ru -i ${PATH_TR}/messages.pot -o ${PATH_TR}/ru/LC_MESSAGES/${domain}.po
                ;;
        update)
                #UPDATE translation tree
                python setup.py update_catalog -l en -i ${PATH_TR}/messages.pot -o ${PATH_TR}/en/LC_MESSAGES/${domain}.po
                python setup.py update_catalog -l ru -i ${PATH_TR}/messages.pot -o ${PATH_TR}/ru/LC_MESSAGES/${domain}.po
                ;;
       compile)
                #Compile to *.po to *.mo
                python setup.py compile_catalog --directory ${PATH_TR} --domain ${domain}
                ;;
             *)
                echo "${0##*/} {extract|init|update|compile}"
                RETVAL=1
esac

exit $RETVAL

python setup.py extract_messages 

#Init tarnslation tree
python setup.py init_catalog -l en -i ${PATH_TR}/messages.pot -o ${PATH_TR}/en/LC_MESSAGES/${domain}.po
python setup.py init_catalog -l ru -i ${PATH_TR}/messages.pot -o ${PATH_TR}/ru/LC_MESSAGES/${domain}.po

#UPDATE translation tree
python setup.py update_catalog -l en -i ${PATH_TR}/messages.pot -o ${PATH_TR}/en/LC_MESSAGES/${domain}.po
python setup.py update_catalog -l ru -i ${PATH_TR}/messages.pot -o ${PATH_TR}/ru/LC_MESSAGES/${domain}.po

#Compile to *.po to *.mo
python setup.py compile_catalog --directory ${PATH_TR} --domain ${domain}



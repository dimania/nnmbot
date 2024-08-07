#!/bin/sh +x
#
# bash scripts for create i18n   
#
domain=nnmbot
PATH_TR="../locales"
PATH_IN=".."
RETVAL=0



case "$1" in
        extract)
                if ! [ -d $PATH_TR ]; then
                   mkdir $PATH_TR
                fi
                python setup.py extract_messages --output-file ${PATH_TR}/messages.pot --input-paths ${PATH_IN} --omit-header --no-wrap
                ;;
          init)
                #Init tarnslation tree
                if ! [ -d $PATH_TR ]; then
                   mkdir $PATH_TR
                fi
                python setup.py init_catalog -l en -i ${PATH_TR}/messages.pot -o ${PATH_TR}/en/LC_MESSAGES/${domain}.po
                python setup.py init_catalog -l ru -i ${PATH_TR}/messages.pot -o ${PATH_TR}/ru/LC_MESSAGES/${domain}.po
                ;;
        update)
                #UPDATE translation tree
                if ! [ -d $PATH_TR ]; then
                   echo no dir $PATH_TR nothing update - Begin run ini or extract
                   RETVAL=1
                   exit $RETVAL
                fi
                python setup.py update_catalog -l en -i ${PATH_TR}/messages.pot -o ${PATH_TR}/en/LC_MESSAGES/${domain}.po
                python setup.py update_catalog -l ru -i ${PATH_TR}/messages.pot -o ${PATH_TR}/ru/LC_MESSAGES/${domain}.po
                ;;
       compile)
                #Compile to *.po to *.mo
                if ! [ -d $PATH_TR ]; then
                   echo no dir $PATH_TR nothing compile - Begin run ini or extract
                   RETVAL=1
                   exit $RETVAL
                fi
                python setup.py compile_catalog --directory ${PATH_TR} --domain ${domain}
                ;;
             *)
                echo "Sequence:"
                echo "1. ectract - exctract from code" 
                echo "2. update - update translation files - add no translate stirngs"
                echo "3. compile - compile to end point"
                echo "init - only first once time when not translation yet"
                echo "${0##*/} {extract|init|update|compile}"
                RETVAL=1
esac

exit $RETVAL



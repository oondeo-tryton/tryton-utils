#!/bin/bash

host_from=""
host_to="localhost"
db=""
tmpdb="nan_tmp_product_product"
pgsql_orig_port=5432
pgsql_dest_port=5432
pgsql_orig_user=""
limit=""
full_backup=0
date=`date +"%y%m%d"`
dest_dir="/tmp"

function help()
{
    echo "The database will be dump in to 2 files, the data and the schema. To restore it first restore the schema after the data"
    echo "Tha will be done with this structe, to dump the database without the audittrail and the attacheds files"
    echo
    echo "Usage:"
    echo "    $0 [options...]"
	echo
	echo "Options:"
    echo "    -O <origin_host>: (Required) Where we take the db from. Leave a copy in the home directory of the user used. Normally administrator. For a local db copy, type 'localhost'."
	echo "    -D <destination_host>: Where leave the db. (all the db will be stored in the $dest_dir directories). By default local copy."
    echo "    -d <dbname>: (Required) the db name to dump."
    echo "    -p <pgsql_orig_port>: by default $pgsql_orig_port."
    echo "    -P <pgsql_dest_port>: by default $pgsql_dest_port."
    echo "    -u <pgsql_orig_user>: the user used in the remote database connection. If not specified, it uses the Unix user (peer identification)"
    echo "    -l <scp_limit>: Limits the used bandwidth, specified in Kbit/s. By default no limits."
                # -3 = Copies between two remote hosts are transferred through the local host.
                #      Without this option the data is copied directly between the two remote hosts.
                #      Note that this option disables the progress meter.
    echo "    -f <dest_dir>: Type the directory where to copy the db structure and the script to restore it. Default value is $dest_dir."
    echo "    -o: The db is from a oscommerce project."
	echo "    -a: Full backup. Backup all in one file, not diveded by schema and data."
    echo "        If this option is selected the limit option is required and the oscommerce option is ignored."
    echo "        You need to have installed the 7z compressor."

    exit 1
}

while getopts O:D:d:p:P:u:l:f:oa x; do
    case "$x" in
        O) host_from="$OPTARG";;
        D) host_to="$OPTARG";;
        d) db="$OPTARG";;
        p) pgsql_orig_port="$OPTARG";;
        P) pgsql_dest_port="$OPTARG";;
        u) pgsql_orig_user="-U $OPTARG";;
        l) limit="-l $OPTARG";;
        f) dest_dir="$OPTARG";;
        a) full_backup=1;;
        [?]) help;;
    esac
done

if [ "$host_to" != "localhost" ]; then
    dest="$host_to:$dest_dir"
else
    dest="$dest_dir"
fi

if [ -z "$host_from" -o -z "$db" ]; then
    help
fi

if [ $full_backup -eq 1 ]; then
    if [ -z "$limit" ]; then
        echo "-------   WITH A FULL BACKUP, LIMIT IS REQUIRED   -------"
        echo
        help
    fi

    if [ -f "/sbin/start-stop-daemon" ]; then # debian system
        if [ "$host_from" == "localhost" ]; then
            if [ ! -f "/usr/bin/7z" ]; then
                echo "-------   YOU NEED A DEBIAN SYSTEM AND HAVE THE 7z COMPRESSOR INSTALLED   -------"
                echo
                help
            fi
        else
            compress=`ssh $host_from "ls -1 /usr/bin/7z"`
            if [ "$compress" != "/usr/bin/7z" ]; then
                echo "-------   YOU NEED A DEBIAN SYSTEM AND HAVE THE 7z COMPRESSOR INSTALLED IN $host_from HOST   -------"
                echo
                help
            fi
        fi
    fi
fi

prefix=$db"_"$date
backup_schema="$prefix.schema.backup"
backup_data="$prefix.data.backup"
backup_all="$prefix.backup"
backup_all_7z="$prefix.backup.7z"

# OLD from OpenERP
# exclude_table="--exclude-table=ir_attachment --exclude-table=nan_document --exclude-table=ir_documentation_screenshot --exclude-table=audittrail_log --exclude-table=audittrail_log_line --exclude-table=audittail_rules_users --exclude-table=audittrail_rule"
exclude_table=""

if [ $full_backup -eq 1 ]; then
    echo "#######   CREATING A FULL BACKUP OF THE $db DATABASE FROM $host_from HOST...   #######"
    echo "#######   REMEMBER THAT THIS OPERATION COULD TAKE A LOT OF TIME   #######"
    echo
    echo "#######   DUMPING THE $db DATABASE FROM $host_from HOST...   #######"
    if [ "$host_from" == "localhost" ]; then
        pg_dump $pgsql_orig_user -p $pgsql_orig_port --no-owner --file=/tmp/$backup_all $db
        echo "#######   COMPRESSING THE $backup_all DB...   #######"
        /usr/bin/7z a /tmp/$backup_all_7z /tmp/$backup_all
    else
        ssh $host_from "pg_dump $pgsql_orig_user -p $pgsql_orig_port --no-owner --file=backups/$backup_all $db"
        echo "#######   COMPRESSING THE $backup_all DB...   #######"
        ssh $host_from "/usr/bin/7z a backups/$backup_all_7z backups/$backup_all"
    fi

    echo "#######   COPYING THE $backup_all_7z FILE FROM $host_from TO $dest_dir DIRECTORY OF $host_to...   #######"
    if [ "$host_from" == "localhost" ]; then
        scp $limit /tmp/$backup_all_7z $dest
    else
        scp -3 $limit $host_from:./backups/$backup_all_7z $dest
    fi

    echo "#######   ALL IS DONE   #######"
else
    echo "#######   DUMPING THE SCHEMA OF THE $db DATABASE FROM $host_from HOST...   #######"
    if [ "$host_from" == "localhost" ]; then
        pg_dump $pgsql_orig_user -p $pgsql_orig_port --schema-only --no-owner --file=/tmp/$backup_schema $db
    else
        ssh $host_from "pg_dump $pgsql_orig_user -p $pgsql_orig_port --schema-only --no-owner --file=backups/$backup_schema $db"
    fi

    echo "#######   DUMPING THE DATA OF THE $db DATABASE FROM $host_from HOST...   #######"
    if [ "$host_from" == "localhost" ]; then
        pg_dump $pgsql_orig_user -p $pgsql_orig_port --format=c --data-only --no-owner --disable-triggers $exclude_table --file=/tmp/$backup_data $db
    else
        ssh $host_from "pg_dump $pgsql_orig_user -p $pgsql_orig_port --format=c --data-only --no-owner --disable-triggers $exclude_table --file=backups/$backup_data $db"
    fi

    echo "#######   COPYING THE $backup_data FILE FROM $host_from TO $dest_dir DIRECTORY OF $host_to...   #######"
    if [ "$host_from" == "localhost" ]; then
        scp $limit /tmp/$backup_data $dest
    else
        scp -3 $limit $host_from:./backups/$backup_data $dest
    fi

    echo "#######   COPYING THE $backup_schema FILE FROM $host_from TO $dest_dir DIRECTORY OF $host_to...   #######"
    if [ "$host_from" == "localhost" ]; then
        scp $limit /tmp/$backup_schema $dest
    else
        scp -3 $limit $host_from:./backups/$backup_schema $dest
    fi

    echo "#######   ALL IS DONE   #######"
fi

restore_file="restore_$prefix.nan"
if [ "$host_to" != "localhost" ]; then
    restore_db="/tmp/$restore_file"
else
    restore_db="$dest/$restore_file"
fi

echo "#!/bin/bash" > $restore_db
echo >> $restore_db
echo "echo \"#######   STARTING $db RESTORE INTO $prefix DB...   #######\"" >> $restore_db
echo "createdb -p $pgsql_dest_port $prefix" >> $restore_db
if [ $full_backup -eq 1 ]; then
    echo "/usr/bin/7z x $backup_all_7z" >> $restore_db
    echo "psql -p $pgsql_dest_port $prefix < backups/$backup_all" >> $restore_db
else
    echo "psql -p $pgsql_dest_port $prefix < $backup_schema" >> $restore_db
    echo "pg_restore -p $pgsql_dest_port --dbname=$prefix --disable-triggers -j 3 $backup_data" >> $restore_db
fi
echo "echo \"Disabling imap and smtp servers...\""
echo "psql -p $pgsql_dest_port $prefix -c \"update imap_server set state = 'draft';\"" >> $restore_db
echo "psql -p $pgsql_dest_port $prefix -c \"update smtp_server set state = 'draft';\"" >> $restore_db
echo "psql -p $pgsql_dest_port $prefix -c \"update ir_cron set active = False;\"" >> $restore_db
echo "psql -p $pgsql_dest_port $prefix -c \"update ir_trigger set active = False;\"" >> $restore_db

echo "echo \"#######   END   #######\"" >> $restore_db
echo "exit 0" >> $restore_db

chmod 744 $restore_db
if [ "$host_to" != "localhost" ]; then
    scp $limit $restore_db $dest
fi
echo
echo
echo "TO RESTORE THE $db DB, YOU HAVE TO DO IN THE $host_to HOST:"
echo "    ./restore_$prefix.nan"
echo "A NEW DB CALLED $prefix WILL BE CREATED"

exit 0

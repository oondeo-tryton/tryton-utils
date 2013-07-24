#!/usr/bin/env python
import psycopg2

tables=[('timesheet_work','parent')]

def _parent_store_compute(cr, table, field):
        def browse_rec(root, pos=0):
            where = field + '=' + str(root)

            if not root:
                where = parent_field + 'IS NULL'

            cr.execute('SELECT id FROM %s WHERE %s \
                ORDER BY %s' % (table, where, field))
            pos2 = pos + 1
            childs = cr.fetchall()
            for id in childs:
                pos2 = browse_rec(id[0], pos2)
            cr.execute('update %s set "left"=%s, "right"=%s\
                where id=%s' % (table, pos, pos2, root))
            return pos2 + 1

        query = 'SELECT id FROM %s WHERE %s IS NULL order by %s' % (
            table, field, field)
        pos = 0
        cr.execute(query)
        for (root,) in cr.fetchall():
            pos = browse_rec(root, pos)
        return True


def calc_parent_leftright(targetCR):

    for table, field in tables:
        print "calculating parent_left of table", table, "and field:", field
        _parent_store_compute(targetCR, table, field)



if __name__ == '__main__':
    database = 'project'
    database_type = 'postgresql'
    password = 'admin'
    print "hola"
    redmineDB = psycopg2.connect(
        dbname = database,
        host = 'localhost',
        port = 5432,
        user = 'angel')

    print "hola2"
    cursor = redmineDB.cursor()
    calc_parent_leftright(cursor)

    redmineDB.commit()
    redmineDB.close()


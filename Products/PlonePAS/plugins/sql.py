"""
demo sql plugin for roles, and properties (string only) plugins
"""

sql_ddl = """
create table p_users (
   user_id   integer primary key,
   login     varchar(100),
   );

create table p_user_role_map (
   role_id   integer references p_roles( role_id ),
   user_id   integer references p_users( user_id )
   );

create table p_roles (
   role_id   integer primary key,
   role_name varchar(100)
   );

create table p_groups (
    group_id integer primary key,
    group_name varchar(100)
    );

create table p_group_user_map (
    group_id integer references p_groups( group_id ),
    user_id  integer references p_users( user_id )
    );

create table p_group_role_map (
    group_id integer references p_group( group_id ),
    role_id integer references p_roles( role_id )
    );

create table p_user_properties (
    user_id integer references p_users( user_id )
    key varchar(100),
    value varchar(2000)
    );
"""

sql_get_groups_for_user = """
select pg.group_name
from p_groups pg, p_users pu
where pg.user_id = pu.user_id
  and pu.user_id = '%s'
"""

sql_get_properties_for_user = """
select pp.*
from p_user_properties pp, p_users pu
where pp.user_id = pu.user_id
  and pu.user_id = '%s'
"""

sql_get_roles_for_user = """
select pr.role_name
from p_roles pr,
     p_users pu,
     p_user_role_map purm
where pr.role_id = purm.role_id
  and purm.user_id = pu.user_id
  and pu.user_id = '%s'
"""

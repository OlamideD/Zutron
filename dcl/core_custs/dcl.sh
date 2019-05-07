#!/usr/bin/env bash

root_path="/home/frappe/frappe-bench"
full_path=$root_path"/apps/dcl/dcl/core_custs/erpnext/footer_powered.html"
full_path_dest=$root_path"/apps/erpnext/erpnext/templates/includes/footer/footer_powered.html"
cp $full_path $full_path_dest
cp $root_path/apps/dcl/dcl/core_custs/erpnext/footer_extension.html $root_path/apps/erpnext/erpnext/templates/includes/footer/footer_extension.html
cp $root_path/apps/dcl/dcl/core_custs/erpnext/erp-icon.svg $root_path/apps/erpnext/erpnext/public/images/erp-icon.svg
cp $root_path/apps/dcl/dcl/core_custs/erpnext/favicon.png $root_path/apps/erpnext/erpnext/public/images/favicon.png
cp $root_path/apps/dcl/dcl/core_custs/erpnext/splash.png $root_path/apps/erpnext/erpnext/public/images/splash.png
cp $root_path/apps/dcl/dcl/core_custs/erpnext/erpnext-grey.png $root_path/apps/erpnext/erpnext/public/images/erpnext-grey.png
cp $root_path/apps/dcl/dcl/core_custs/erpnext/erpnext-logo.jpg $root_path/apps/erpnext/erpnext/public/images/erpnext-logo.jpg

cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/accounts.py $root_path/apps/erpnext/erpnext/config/accounts.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/buying.py $root_path/apps/erpnext/erpnext/config/buying.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/crm.py $root_path/apps/erpnext/erpnext/config/crm.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/hr.py $root_path/apps/erpnext/erpnext/config/hr.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/manufacturing.py $root_path/apps/erpnext/erpnext/config/manufacturing.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/projects.py $root_path/apps/erpnext/erpnext/config/projects.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/selling.py $root_path/apps/erpnext/erpnext/config/selling.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/setup.py $root_path/apps/erpnext/erpnext/config/setup.py
cp $root_path/apps/dcl/dcl/core_custs/erpnext/config/stock.py $root_path/apps/erpnext/erpnext/config/stock.py



cd &&
cd frappe-bench &&
rm -f $root_path/apps/erpnext/erpnext/config/accounts.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/buying.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/crm.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/hr.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/manufacturing.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/projects.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/selling.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/setup.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/stock.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/learn.pyc &&
rm -f $root_path/apps/erpnext/erpnext/config/learn.py &&
bench migrate &&
bench build &&
bench clear-cache &&
bench restart &&
echo "Success!"
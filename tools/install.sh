#!/usr/bin/env bash
MYDIR=$(dirname $0)

if [ "`whoami`" != "root" ]; then
  echo "Require root privilege"
  exit 1
fi

TOOLS_DIR=${MYDIR}
SRC_DIR=${MYDIR}/../src
INSTALL_DIR=/opt/usbdevicechecker
EXEC_NAME=usbdevicechecker.py
SERVICE_DIR=/lib/systemd/system
SERVICE_NAME=usbdevicechecker.service

mkdir -p ${INSTALL_DIR}
cp ${SRC_DIR}/*.py ${INSTALL_DIR}/.
chown root:root ${INSTALL_DIR}/*.py
chmod 544 ${INSTALL_DIR}/${EXEC_NAME}

cat - > ${SERVICE_DIR}/${SERVICE_NAME} << _EOF_
[Unit]
Description=USB device checker

[Service]
Type=exec
ExecStart=${INSTALL_DIR}/${EXEC_NAME}

[Install]
WantedBy=multi-user.target
_EOF_
chown root:root ${SERVICE_DIR}/${SERVICE_NAME}
chmod 644 ${SERVICE_DIR}/${SERVICE_NAME}

systemctl daemon-reload
systemctl enable ${SERVICE_NAME}
systemctl start ${SERVICE_NAME}

exit 0

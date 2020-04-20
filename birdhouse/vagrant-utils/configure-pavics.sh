#!/bin/sh -x

if [ ! -f env.local ]; then
    cp env.local.example env.local
    cat <<EOF >> env.local

# override with values needed for vagrant
export SSL_CERTIFICATE='./certkey.pem'  # path to the nginx ssl certificate, path and key bundle
export PAVICS_FQDN='${VM_HOSTNAME}.$VM_DOMAIN' # Fully qualified domain name of this Pavics installation
EOF
    if [ -n "$LETSENCRYPT_EMAIL" ]; then
    cat <<EOF >> env.local
export SUPPORT_EMAIL="$LETSENCRYPT_EMAIL"
EOF
    fi

    if [ -n "$KITENAME" -a -n "$KITESUBDOMAIN" ]; then
    cat <<EOF >> env.local
export PAVICS_FQDN_PUBLIC="$KITESUBDOMAIN-$KITENAME"
export ALLOW_UNSECURE_HTTP="True"
EOF
    fi
else
    echo "existing env.local file, not overriding"
fi

if [ ! -f certkey.pem ]; then
    . ./env.local
    if [ -n "$LETSENCRYPT_EMAIL" ]; then
        deployment/certbotwrapper --cert-name $PAVICS_FQDN
        CERTPATH="/etc/letsencrypt/live/$PAVICS_FQDN"
        sudo cat $CERTPATH/fullchain.pem $CERTPATH/privkey.pem > $SSL_CERTIFICATE
    else
        openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out cert.pem \
            -subj "/C=CA/ST=Quebec/L=Montreal/O=RnD/CN=${VM_HOSTNAME}.$VM_DOMAIN"
        cp cert.pem certkey.pem
        cat key.pem >> certkey.pem
        if [ -z "$VERIFY_SSL" ]; then
            cat <<EOF >> env.local
export VERIFY_SSL="false"
EOF
        fi
    fi
else
    echo "existing certkey.pem file, not overriding"
fi

./pavics-compose.sh up -d

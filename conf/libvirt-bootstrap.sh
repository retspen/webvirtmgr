#!/bin/sh -
#===============================================================================
# vim: softtabstop=4 shiftwidth=4 expandtab fenc=utf-8 spell spelllang=en cc=81
#===============================================================================
#
#          FILE: bootstrap-webvirtmgr.sh
#
#   DESCRIPTION: Bootstrap webvirtmgr installation for various distributions
#
#          BUGS: https://github.com/retspen/webvirtmgr-boostrap/issues
#
#     COPYRIGHT: (c) 2013 by the WebVirtMgr Team
#
#       LICENSE: Apache 2.0
#  ORGANIZATION: WebVirtMgr (webvirtmgr.net)
#       CREATED: 11/11/2013 11:00:00 EET
#===============================================================================

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  echoerr
#   DESCRIPTION:  Echo errors to stderr.
#-------------------------------------------------------------------------------
echoerror() {
    printf "${RC} * ERROR${EC}: $@\n" 1>&2;
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  echoinfo
#   DESCRIPTION:  Echo information to stdout.
#-------------------------------------------------------------------------------
echoinfo() {
    printf "${GC} *  INFO${EC}: %s\n" "$@";
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  echowarn
#   DESCRIPTION:  Echo warning informations to stdout.
#-------------------------------------------------------------------------------
echowarn() {
    printf "${YC} *  WARN${EC}: %s\n" "$@";
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  echodebug
#   DESCRIPTION:  Echo debug information to stdout.
#-------------------------------------------------------------------------------
echodebug() {
    if [ $_ECHO_DEBUG -eq $BS_TRUE ]; then
        printf "${BC} * DEBUG${EC}: %s\n" "$@";
    fi
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __test_distro_arch
#   DESCRIPTION:  Echo errors to stderr.
#-------------------------------------------------------------------------------
__test_distro_arch() {
    ARCH=$(uname -m | sed 's/x86_//;s/i[3-6]86/32/')
    if [ "$ARCH" = 32 ]; then
        echoerror "32-bit Arch kernel does not support"
        exit 1
    fi
}
__test_distro_arch

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __strip_duplicates
#   DESCRIPTION:  Strip duplicate strings
#-------------------------------------------------------------------------------
__strip_duplicates() {
    echo $@ | tr -s '[:space:]' '\n' | awk '!x[$0]++'
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __function_defined
#   DESCRIPTION:  Checks if a function is defined within this scripts scope
#    PARAMETERS:  function name
#       RETURNS:  0 or 1 as in defined or not defined
#-------------------------------------------------------------------------------
__function_defined() {
    FUNC_NAME=$1
    if [ "$(command -v $FUNC_NAME)x" != "x" ]; then
        echoinfo "Found function $FUNC_NAME"
        return 0
    fi
    echodebug "$FUNC_NAME not found...."
    return 1
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __parse_version_string
#   DESCRIPTION:  Parse version strings ignoring the revision.
#                 MAJOR.MINOR.REVISION becomes MAJOR.MINOR
#-------------------------------------------------------------------------------
__parse_version_string() {
    VERSION_STRING="$1"
    PARSED_VERSION=$(
        echo $VERSION_STRING |
        sed -e 's/^/#/' \
            -e 's/^#[^0-9]*\([0-9][0-9]*\.[0-9][0-9]*\)\(\.[0-9][0-9]*\).*$/\1/' \
            -e 's/^#[^0-9]*\([0-9][0-9]*\.[0-9][0-9]*\).*$/\1/' \
            -e 's/^#[^0-9]*\([0-9][0-9]*\).*$/\1/' \
            -e 's/^#.*$//'
    )
    echo $PARSED_VERSION
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __sort_release_files
#   DESCRIPTION:  Custom sort function. Alphabetical or numerical sort is not
#                 enough.
#-------------------------------------------------------------------------------
__sort_release_files() {
    KNOWN_RELEASE_FILES=$(echo "(arch|centos|debian|ubuntu|fedora|redhat|suse|\
        mandrake|mandriva|gentoo|slackware|turbolinux|unitedlinux|lsb|system|\
        os)(-|_)(release|version)" | sed -r 's:[[:space:]]::g')
    primary_release_files=""
    secondary_release_files=""
    # Sort know VS un-known files first
    for release_file in $(echo $@ | sed -r 's:[[:space:]]:\n:g' | sort --unique --ignore-case); do
        match=$(echo $release_file | egrep -i ${KNOWN_RELEASE_FILES})
        if [ "x${match}" != "x" ]; then
            primary_release_files="${primary_release_files} ${release_file}"
        else
            secondary_release_files="${secondary_release_files} ${release_file}"
        fi
    done

    # Now let's sort by know files importance, max important goes last in the max_prio list
    max_prio="redhat-release centos-release"
    for entry in $max_prio; do
        if [ "x$(echo ${primary_release_files} | grep $entry)" != "x" ]; then
            primary_release_files=$(echo ${primary_release_files} | sed -e "s:\(.*\)\($entry\)\(.*\):\2 \1 \3:g")
        fi
    done
    # Now, least important goes last in the min_prio list
    min_prio="lsb-release"
    for entry in $max_prio; do
        if [ "x$(echo ${primary_release_files} | grep $entry)" != "x" ]; then
            primary_release_files=$(echo ${primary_release_files} | sed -e "s:\(.*\)\($entry\)\(.*\):\1 \3 \2:g")
        fi
    done

    # Echo the results collapsing multiple white-space into a single white-space
    echo "${primary_release_files} ${secondary_release_files}" | sed -r 's:[[:space:]]:\n:g'
}

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __gather_linux_system_info
#   DESCRIPTION:  Discover Linux system information
#-------------------------------------------------------------------------------
__gather_linux_system_info() {
    DISTRO_NAME=""
    DISTRO_VERSION=""

    # Let's test if the lsb_release binary is available
    rv=$(lsb_release >/dev/null 2>&1)
    if [ $? -eq 0 ]; then
        DISTRO_NAME=$(lsb_release -si)
        if [ "x$(echo "$DISTRO_NAME" | grep RedHat)" != "x" ]; then
            # Let's convert CamelCase to Camel Case
            DISTRO_NAME=$(__camelcase_split "$DISTRO_NAME")
        fi
        if [ "${DISTRO_NAME}" = "openSUSE project" ]; then
            # lsb_release -si returns "openSUSE project" on openSUSE 12.3
            DISTRO_NAME="opensuse"
        fi
        if [ "${DISTRO_NAME}" = "SUSE LINUX" ]; then
            # lsb_release -si returns "SUSE LINUX" on SLES 11 SP3
            DISTRO_NAME="suse"
        fi
        rv=$(lsb_release -sr)
        [ "${rv}x" != "x" ] && DISTRO_VERSION=$(__parse_version_string "$rv")
    elif [ -f /etc/lsb-release ]; then
        # We don't have the lsb_release binary, though, we do have the file it parses
        DISTRO_NAME=$(grep DISTRIB_ID /etc/lsb-release | sed -e 's/.*=//')
        rv=$(grep DISTRIB_RELEASE /etc/lsb-release | sed -e 's/.*=//')
        [ "${rv}x" != "x" ] && DISTRO_VERSION=$(__parse_version_string "$rv")
    fi

    if [ "x$DISTRO_NAME" != "x" ] && [ "x$DISTRO_VERSION" != "x" ]; then
        # We already have the distribution name and version
        return
    fi

    for rsource in $(__sort_release_files $(
            cd /etc && /bin/ls *[_-]release *[_-]version 2>/dev/null | env -i sort | \
            sed -e '/^redhat-release$/d' -e '/^lsb-release$/d'; \
            echo redhat-release lsb-release
            )); do

        [ -L "/etc/${rsource}" ] && continue        # Don't follow symlinks
        [ ! -f "/etc/${rsource}" ] && continue      # Does not exist

        n=$(echo ${rsource} | sed -e 's/[_-]release$//' -e 's/[_-]version$//')
        rv=$( (grep VERSION /etc/${rsource}; cat /etc/${rsource}) | grep '[0-9]' | sed -e 'q' )
        [ "${rv}x" = "x" ] && continue  # There's no version information. Continue to next rsource
        v=$(__parse_version_string "$rv")
        case $(echo ${n} | tr '[:upper:]' '[:lower:]') in
            redhat             )
                if [ ".$(egrep 'CentOS' /etc/${rsource})" != . ]; then
                    n="CentOS"
                elif [ ".$(egrep 'Red Hat Enterprise Linux' /etc/${rsource})" != . ]; then
                    n="<R>ed <H>at <E>nterprise <L>inux"
                else
                    n="<R>ed <H>at <L>inux"
                fi
                ;;
            arch               ) n="Arch Linux"     ;;
            centos             ) n="CentOS"         ;;
            debian             ) n="Debian"         ;;
            ubuntu             ) n="Ubuntu"         ;;
            fedora             ) n="Fedora"         ;;
            suse               ) n="SUSE"           ;;
            system             )
                while read -r line; do
                    [ "${n}x" != "systemx" ] && break
                    case "$line" in
                        *Amazon*Linux*AMI*)
                            n="Amazon Linux AMI"
                            break
                    esac
                done < /etc/${rsource}
                ;;
            os                 )
                nn=$(grep '^ID=' /etc/os-release | sed -e 's/^ID=\(.*\)$/\1/g')
                rv=$(grep '^VERSION_ID=' /etc/os-release | sed -e 's/^VERSION_ID=\(.*\)$/\1/g')
                [ "${rv}x" != "x" ] && v=$(__parse_version_string "$rv") || v=""
                case $(echo ${nn} | tr '[:upper:]' '[:lower:]') in
                    arch        )
                        n="Arch Linux"
                        v=""  # Arch Linux does not provide a version.
                        ;;
                    debian      )
                        n="Debian"
                        if [ "${v}x" = "x" ]; then
                            if [ "$(cat /etc/debian_version)" = "wheezy/sid" ]; then
                                # I've found an EC2 wheezy image which did not tell its version
                                v=$(__parse_version_string "7.0")
                            fi
                        else
                            echowarn "Unable to parse the Debian Version"
                        fi
                        ;;
                    *           )
                        n=${nn}
                        ;;
                esac
                ;;
            *                  ) n="${n}"           ;
        esac
        DISTRO_NAME=$n
        DISTRO_VERSION=$v
        break
    done
}
__gather_linux_system_info

# Simplify distro name naming on functions
DISTRO_NAME_L=$(echo $DISTRO_NAME | tr '[:upper:]' '[:lower:]' | sed 's/[^a-zA-Z0-9_ ]//g' | sed -re 's/([[:space:]])+/_/g')
DISTRO_MAJOR_VERSION="$(echo $DISTRO_VERSION | sed 's/^\([0-9]*\).*/\1/g')"
DISTRO_MINOR_VERSION="$(echo $DISTRO_VERSION | sed 's/^\([0-9]*\).\([0-9]*\).*/\2/g')"
PREFIXED_DISTRO_MAJOR_VERSION="_${DISTRO_MAJOR_VERSION}"
if [ "${PREFIXED_DISTRO_MAJOR_VERSION}" = "_" ]; then
    PREFIXED_DISTRO_MAJOR_VERSION=""
fi
PREFIXED_DISTRO_MINOR_VERSION="_${DISTRO_MINOR_VERSION}"
if [ "${PREFIXED_DISTRO_MINOR_VERSION}" = "_" ]; then
    PREFIXED_DISTRO_MINOR_VERSION=""
fi

#---  FUNCTION  ----------------------------------------------------------------
#          NAME:  __check_end_of_life_versions
#   DESCRIPTION:  Check for end of life distribution versions
#-------------------------------------------------------------------------------
__check_end_of_life_versions() {

    case "${DISTRO_NAME_L}" in
        debian)
            # Debian versions bellow 6 are not supported
            if [ $DISTRO_MAJOR_VERSION -lt 6 ]; then
                echoerror "End of life distributions are not supported."
                echoerror "Please consider upgrading to the next stable. See:"
                echoerror "    https://wiki.debian.org/DebianReleases"
                exit 1
            fi
            ;;

        ubuntu)
            # Ubuntu versions not supported
            #
            #  < 10
            #  = 10.10
            #  = 11.04
            #  = 11.10
            if ([ $DISTRO_MAJOR_VERSION -eq 10 ] && [ $DISTRO_MINOR_VERSION -eq 10 ]) || \
               ([ $DISTRO_MAJOR_VERSION -eq 11 ] && [ $DISTRO_MINOR_VERSION -eq 04 ]) || \
               ([ $DISTRO_MAJOR_VERSION -eq 11 ] && [ $DISTRO_MINOR_VERSION -eq 10 ]) || \
               [ $DISTRO_MAJOR_VERSION -lt 10 ]; then
                echoerror "End of life distributions are not supported."
                echoerror "Please consider upgrading to the next stable. See:"
                echoerror "    https://wiki.ubuntu.com/Releases"
                exit 1
            fi
            ;;

        opensuse)
            # openSUSE versions not supported
            #
            #  <= 12.1
            if ([ $DISTRO_MAJOR_VERSION -eq 12 ] && [ $DISTRO_MINOR_VERSION -eq 1 ]) || [ $DISTRO_MAJOR_VERSION -lt 12 ]; then
                echoerror "End of life distributions are not supported."
                echoerror "Please consider upgrading to the next stable. See:"
                echoerror "    http://en.opensuse.org/Lifetime"
                exit 1
            fi
            ;;

        suse)
            # SuSE versions not supported
            #
            # < 11 SP2
            SUSE_PATCHLEVEL=$(awk '/PATCHLEVEL/ {print $3}' /etc/SuSE-release )
            if [ "x${SUSE_PATCHLEVEL}" = "x" ]; then
                SUSE_PATCHLEVEL="00"
            fi
            if ([ $DISTRO_MAJOR_VERSION -eq 11 ] && [ $SUSE_PATCHLEVEL -lt 02 ]) || [ $DISTRO_MAJOR_VERSION -lt 11 ]; then
                echoerror "Versions lower than SuSE 11 SP2 are not supported."
                echoerror "Please consider upgrading to the next stable"
                exit 1
            fi
            ;;

        fedora)
            # Fedora lower than 18 are no longer supported
            if [ $DISTRO_MAJOR_VERSION -lt 18 ]; then
                echoerror "End of life distributions are not supported."
                echoerror "Please consider upgrading to the next stable. See:"
                echoerror "    https://fedoraproject.org/wiki/Releases"
                exit 1
            fi
            ;;

        centos)
            # CentOS versions lower than 5 are no longer supported
            if ([ $DISTRO_MAJOR_VERSION -eq 6 ] && [ $DISTRO_MINOR_VERSION -lt 3 ]) || [ $DISTRO_MAJOR_VERSION -lt 5 ]; then
                echoerror "End of life distributions are not supported."
                echoerror "Please consider upgrading to the next stable. See:"
                echoerror "    http://wiki.centos.org/Download"
                exit 1
            fi
            ;;

        red_hat*linux)
            # Red Hat (Enterprise) Linux versions lower than 5 are no longer supported
            if ([ $DISTRO_MAJOR_VERSION -eq 6 ] && [ $DISTRO_MINOR_VERSION -lt 3 ]) || [ $DISTRO_MAJOR_VERSION -lt 5 ]; then
                echoerror "End of life distributions are not supported."
                echoerror "Please consider upgrading to the next stable. See:"
                echoerror "    https://access.redhat.com/support/policy/updates/errata/"
                exit 1
            fi
            ;;

        *)
            ;;
    esac
}
# Fail soon for end of life versions
__check_end_of_life_versions


##############################################################################
#
#   CentOS Install Functions
#
install_centos() {
    if [ $DISTRO_MAJOR_VERSION -ge 6 ]; then
        yum -y install qemu-kvm libvirt bridge-utils || return 1
    fi
    return 0
}

install_centos_post() {
    if [ -f /etc/sysconfig/libvirtd ]; then
        sed -i 's/#LIBVIRTD_ARGS/LIBVIRTD_ARGS/g' /etc/sysconfig/libvirtd
    else
        echoerror "/etc/sysconfig/libvirtd not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/libvirtd.conf ]; then
        sed -i 's/#listen_tls/listen_tls/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#listen_tcp/listen_tcp/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#auth_tcp/auth_tcp/g' /etc/libvirt/libvirtd.conf
    else
        echoerror "/etc/libvirt/libvirtd.conf not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/qemu.conf ]; then
        sed -i 's/#vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf
    else
        echoerror "/etc/libvirt/qemu.conf not found. Exiting..."
        exit 1
    fi
    return 0
}

daemons_running_centos() {
    if [ -f /etc/init.d/libvirtd ]; then
        service libvirtd stop > /dev/null 2>&1
        service libvirtd start
    fi
    if [ -f /etc/init.d/libvirt-guests ]; then
        service libvirt-guests stop > /dev/null 2>&1
        service libvirt-guests start
    fi
    if [ -f /usr/lib/systemd/system/libvirtd.service ]; then
        systemctl stop libvirtd.service > /dev/null 2>&1
        systemctl start libvirtd.service
    fi
    if [ -f /usr/lib/systemd/system/libvirt-guests.service ]; then
        systemctl stop libvirt-guests.service > /dev/null 2>&1
        systemctl start libvirt-guests.service
    fi
    return 0
} 
#
#   Ended CentOS Install Functions
#
##############################################################################

##############################################################################
#
#   Fedora Install Functions
#
install_fedora() {
    yum -y install kvm libvirt bridge-utils || return 1
    return 0
}

install_fedora_post() {
    if [ -f /etc/sysconfig/libvirtd ]; then
        sed -i 's/#LIBVIRTD_ARGS/LIBVIRTD_ARGS/g' /etc/sysconfig/libvirtd
    else
        echoerror "/etc/sysconfig/libvirtd not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/libvirtd.conf ]; then
        sed -i 's/#listen_tls/listen_tls/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#listen_tcp/listen_tcp/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#auth_tcp/auth_tcp/g' /etc/libvirt/libvirtd.conf
    else
        echoerror "/etc/libvirt/libvirtd.conf not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/qemu.conf ]; then
        sed -i 's/#vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf
    else
        echoerror "/etc/libvirt/qemu.conf not found. Exiting..."
        exit 1
    fi
    return 0
}

daemons_running_fedora() {
    if [ -f /usr/lib/systemd/system/libvirtd.service ]; then
        systemctl stop libvirtd.service > /dev/null 2>&1
        systemctl start libvirtd.service
    fi
    if [ -f /usr/lib/systemd/system/libvirt-guests.service ]; then
        systemctl stop libvirt-guests.service > /dev/null 2>&1
        systemctl start libvirt-guests.service
    fi
    return 0
} 
#
#   Ended Fedora Install Functions
#
##############################################################################

##############################################################################
#
#   Opensuse Install Functions
#
install_opensuse() {
    zypper -n install -l kvm libvirt bridge-utils || return 1
    return 0
}

install_opensuse_post() {
    if [ -f /etc/sysconfig/libvirtd ]; then
        sed -i 's/#LIBVIRTD_ARGS/LIBVIRTD_ARGS/g' /etc/sysconfig/libvirtd
    else
        echoerror "/etc/sysconfig/libvirtd not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/libvirtd.conf ]; then
        sed -i 's/#listen_tls/listen_tls/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#listen_tcp/listen_tcp/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#auth_tcp/auth_tcp/g' /etc/libvirt/libvirtd.conf
    else
        echoerror "/etc/libvirt/libvirtd.conf not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/qemu.conf ]; then
        sed -i 's/#vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf
    else
        echoerror "/etc/libvirt/qemu.conf not found. Exiting..."
        exit 1
    fi
    return 0
}

daemons_running_opensuse() {
    if [ -f /usr/lib/systemd/system/libvirtd.service ]; then
        systemctl stop libvirtd.service > /dev/null 2>&1
        systemctl start libvirtd.service
    fi
    if [ -f /usr/lib/systemd/system/libvirt-guests.service ]; then
        systemctl stop libvirt-guests.service > /dev/null 2>&1
        systemctl start libvirt-guests.service
    fi
    return 0
}
#
#   Ended openSUSE Install Functions
#
##############################################################################

##############################################################################
#
#   Ubuntu Install Functions
#
install_ubuntu() {
    apt-get update || return 1
    apt-get -y install kvm libvirt-bin bridge-utils sasl2-bin || return 1
    return 0
}

install_ubuntu_post() {
    if [ -f /etc/default/libvirt-bin ]; then
        sed -i 's/libvirtd_opts="-d"/libvirtd_opts="-d -l"/g' /etc/default/libvirt-bin
    else
        echoerror "/etc/default/libvirt-bin not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/libvirtd.conf ]; then
        sed -i 's/#listen_tls/listen_tls/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#listen_tcp/listen_tcp/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#auth_tcp/auth_tcp/g' /etc/libvirt/libvirtd.conf
    else
        echoerror "/etc/libvirt/libvirtd.conf not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/qemu.conf ]; then
        if ([ $DISTRO_MAJOR_VERSION -eq 12 ] && [ $DISTRO_MINOR_VERSION -eq 04 ]); then
            sed -i 's/# vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf
        else
            sed -i 's/#vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf
        fi
    else
        echoerror "/etc/libvirt/qemu.conf not found. Exiting..."
        exit 1
    fi
    return 0
}

daemons_running_ubuntu() {
    if [ -f /etc/init.d/libvirt-bin ]; then
        # Still in SysV init!?
        service libvirt-bin stop > /dev/null 2>&1
        service libvirt-bin start
    fi
    return 0
} 
#
#   Ended Ubuntu Install Functions
#
##############################################################################

##############################################################################
#
#   Debian Install Functions
#
install_debian() {
    apt-get update || return 1
    apt-get -y install kvm libvirt-bin bridge-utils sasl2-bin || return 1
    return 0
}

install_debian_post() {
    if [ $DISTRO_MAJOR_VERSION -ge 8 ]; then
        LIBVIRTSVC=libvirtd
    else
        LIBVIRTSVC=libvirt-bin
    fi
    if [ -f /etc/default/$LIBVIRTSVC ]; then
        if [ "$( grep -c '^libvirtd_opts *=' /etc/default/$LIBVIRTSVC )" -gt 0 ]; then
            if [ $( grep -c '^libvirtd_opts *=.*-l' /etc/default/$LIBVIRTSVC ) -eq 0 ]; then
                sed -i 's/^libvirtd_opts="\([^"]*\)"/libvirtd_opts="\1 -l"/g' /etc/default/$LIBVIRTSVC
            fi
        else
            sed -i 's/^#libvirtd_opts=.*$/libvirtd_opts="-l"/g' /etc/default/$LIBVIRTSVC
        fi
    else
        echoerror "/etc/default/$LIBVIRTSVC not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/libvirtd.conf ]; then
        sed -i 's/#listen_tls/listen_tls/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#listen_tcp/listen_tcp/g' /etc/libvirt/libvirtd.conf
        sed -i 's/#auth_tcp/auth_tcp/g' /etc/libvirt/libvirtd.conf
    else
        echoerror "/etc/libvirt/libvirtd.conf not found. Exiting..."
        exit 1
    fi
    if [ -f /etc/libvirt/qemu.conf ]; then
        sed -i 's/# vnc_listen/vnc_listen/g' /etc/libvirt/qemu.conf
    else
        echoerror "/etc/libvirt/qemu.conf not found. Exiting..."
        exit 1
    fi
    return 0
}

daemons_running_debian() {
    if [ $DISTRO_MAJOR_VERSION -ge 8 ]; then
        LIBVIRTSVC=libvirtd
    else
        LIBVIRTSVC=libvirt-bin
    fi
    if [ -f /etc/init.d/$LIBVIRTSVC ]; then
        /etc/init.d/$LIBVIRTSVC stop > /dev/null 2>&1
        /etc/init.d/$LIBVIRTSVC start
    fi
    return 0
} 
#
#   Ended Debian Install Functions
#
##############################################################################

#=============================================================================
# INSTALLATION
#=============================================================================
# Let's get the install function
INSTALL_FUNC_NAMES="install_${DISTRO_NAME_L}"

INSTALL_FUNC="null"
for FUNC_NAME in $(__strip_duplicates $INSTALL_FUNC_NAMES); do
    if __function_defined $FUNC_NAME; then
        INSTALL_FUNC=$FUNC_NAME
        break
    fi
done
echodebug "INSTALL_FUNC=${INSTALL_FUNC}"

if [ $INSTALL_FUNC = "null" ]; then
    echoerror "No installation function found. Exiting..."
    exit 1
else
    echoinfo "Running ${INSTALL_FUNC}()"
    $INSTALL_FUNC
    if [ $? -ne 0 ]; then
        echoerror "Failed to run ${INSTALL_FUNC}()!!!"
        exit 1
    fi
fi

# Let's get the post install function
POST_FUNC_NAMES="install_${DISTRO_NAME_L}_post"

POST_INSTALL_FUNC="null"
for FUNC_NAME in $(__strip_duplicates $POST_FUNC_NAMES); do
    if __function_defined $FUNC_NAME; then
        POST_INSTALL_FUNC=$FUNC_NAME
        break
    fi
done
echodebug "POST_INSTALL_FUNC=${POST_INSTALL_FUNC}"

if [ $POST_INSTALL_FUNC = "null" ]; then
    echoerror "No installation function found. Exiting..."
    exit 1
else
    echoinfo "Running ${POST_INSTALL_FUNC}()"
    $POST_INSTALL_FUNC
    if [ $? -ne 0 ]; then
        echoerror "Failed to run ${POST_INSTALL_FUNC}()!!!"
        exit 1
    fi
fi

# Let's get the daemons running check function.
DAEMONS_RUNNING_FUNC_NAMES="daemons_running_${DISTRO_NAME_L}"

DAEMONS_RUNNING_FUNC="null"
for FUNC_NAME in $(__strip_duplicates $DAEMONS_RUNNING_FUNC_NAMES); do
    if __function_defined $FUNC_NAME; then
        DAEMONS_RUNNING_FUNC=$FUNC_NAME
        break
    fi
done
echodebug "DAEMONS_RUNNING_FUNC=${DAEMONS_RUNNING_FUNC}"

if [ $DAEMONS_RUNNING_FUNC = "null" ]; then
    echoerror "No installation function found. Exiting..."
    exit 1
else
    echoinfo "Running ${DAEMONS_RUNNING_FUNC}()"
    $DAEMONS_RUNNING_FUNC
    if [ $? -ne 0 ]; then
        echoerror "Failed to run ${DAEMONS_RUNNING_FUNC}()!!!"
        exit 1
    fi
fi

exit 0

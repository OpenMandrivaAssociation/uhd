Name:           uhd
URL:            http://code.ettus.com/redmine/ettus/projects/uhd/wiki
Version:        3.4.1
Release:        1
Group:          Communications
Summary:        Universal Hardware Driver for Ettus Research products
License:        GPLv3+
Source0:        %{name}-%{version}.tar.gz
# Create tarball from git with:
# $ make-tarball uhd git://code.ettus.com/ettus/uhd.git
# See note in make-tarball script
Source1:	make-tarball

BuildRequires:  cmake
BuildRequires:  boost-devel
BuildRequires:  libusb1-devel
BuildRequires:  liborc-devel
BuildRequires:  python-cheetah
BuildRequires:  python-docutils
BuildRequires:  doxygen
BuildRequires:  pkgconfig

%description
The UHD is the universal hardware driver for Ettus Research products.
The goal of the UHD is to provide a host driver and API for current and
future Ettus Research products. It can be used standalone without GNU Radio.

%prep
%setup -q

%build
mkdir -p host/build
cd host/build
cmake ../ -DCMAKE_INSTALL_PREFIX=/usr 
%make

%check
cd host/build
make test

%install
pushd host/build
make install DESTDIR=%{buildroot}

# Allow access only to users in usrp group
sed -i 's/MODE:="0666"/MODE:="0660"/' %{buildroot}%{_datadir}/uhd/utils/uhd-usrp.rules
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d
mv %{buildroot}%{_datadir}/uhd/utils/uhd-usrp.rules %{buildroot}%{_sysconfdir}/udev/rules.d/10-usrp-uhd.rules

# Remove binaries for tests, examples
rm -rf %{buildroot}%{_datadir}/uhd/{tests,examples}

# Move the utils stuff to libexec dir
mkdir -p %{buildroot}%{_libexecdir}/uhd
mv %{buildroot}%{_datadir}/uhd/utils/* %{buildroot}%{_libexecdir}/uhd

popd
# Package base docs to base package
mkdir _tmpdoc
mv %{buildroot}%{_docdir}/%{name}/{AUTHORS.txt,LICENSE.txt,README.txt} _tmpdoc

%package devel
Summary:        Development files for UHD
Group:          Communications
Requires:       %{name} = %{version}-%{release}

%description devel
Development files for the Universal Hardware Driver (UHD).

%package doc
Summary:        Documentation files for UHD
Group:          Communications
BuildArch:      noarch

%description doc
Documentation for the Universal Hardware Driver (UHD).

%pre -n uhd
getent group usrp >/dev/null || groupadd -r usrp

%files
%{_bindir}/*
%config(noreplace) %{_sysconfdir}/udev/rules.d/10-usrp-uhd.rules
%{_libdir}/lib*.so.*
%{_libexecdir}/uhd

%files devel
%{_includedir}/*
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc

%files doc
%doc _tmpdoc/*
%{_docdir}/%{name}/manual/*/*
%{_docdir}/%{name}/doxygen/*/*

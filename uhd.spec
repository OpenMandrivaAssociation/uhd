%define _disable_lto %nil

Name:           uhd
URL:            https://github.com/EttusResearch/uhd
Version:        3.14.0.0
Release:        1
Summary:        Universal Hardware Driver for Ettus Research products
License:        GPLv3+
Source0:	https://github.com/EttusResearch/uhd/archive/v%{version}.tar.gz
Source100:      uhd.rpmlintrc

BuildRequires:  cmake
BuildRequires:  boost-devel
BuildRequires:  pkgconfig(libusb-1.0)
BuildRequires:  pkgconfig(udev)
BuildRequires:  doxygen
BuildRequires:	python-mako
BuildRequires:	python-docutils

%description
The UHD is the universal hardware driver for Ettus Research products.
The goal of the UHD is to provide a host driver and API for current and
future Ettus Research products. It can be used standalone without GNU Radio.

%prep
%autosetup -p1

%build
cd host
mkdir build
pushd build
cmake .. -DENABLE_UTILS=ON \
	-DENABLE_E100=ON \
	-DENABLE_E300=ON \
	-DENABLE_PYTHON3=ON \
	-DENABLE_TESTS=OFF \
	-DENABLE_EXAMPLES=OFF \
	-DPYTHON_EXECUTABLE:FILEPATH=%{__python} \
	-DCMAKE_INSTALL_PREFIX:PATH=%{_prefix} \
        -DCMAKE_INSTALL_LIBDIR:PATH=%{_lib}

%make_build
popd

%check
pushd host
%make_build test -C build

%install
for i in $(grep -rl '%{version}-0-ef798400' .); do sed -i 's!3.14.0.0!%{version}!g' $i;done
pushd host
%make_install -C build

# Allow access only to users in usrp group
sed -i 's/MODE:="0666"/MODE:="0660"/' %{buildroot}%{_libdir}/uhd/utils/uhd-usrp.rules
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d
mv %{buildroot}%{_libdir}/uhd/utils/uhd-usrp.rules %{buildroot}%{_sysconfdir}/udev/rules.d/10-usrp-uhd.rules

# Remove binaries for tests, examples
rm -rf %{buildroot}%{_datadir}/uhd/{tests,examples}

# Move the utils stuff to libexec dir
mkdir -p %{buildroot}%{_libexecdir}/uhd
mv %{buildroot}%{_libdir}/uhd/utils/* %{buildroot}%{_libexecdir}/uhd
popd

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
%{_mandir}/man1/%{name}*.*
%{_mandir}/man1/octo*.*
%{_mandir}/man1/usrp*.*
%config(noreplace) %{_sysconfdir}/udev/rules.d/10-usrp-uhd.rules
%{_libdir}/lib*.so.*
%{_libexecdir}/uhd

%files devel
%{_includedir}/*
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc
%{_libdir}/cmake/uhd/UHDConfig.cmake
%{_libdir}/cmake/uhd/UHDConfigVersion.cmake

%files doc
%{_datadir}/doc/uhd/LICENSE
%{_datadir}/doc/uhd/README.md
%{_docdir}/%{name}/doxygen/*/*
%{_datadir}/%{name}/



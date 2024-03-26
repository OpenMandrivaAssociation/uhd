#% global debug_package %{nil}
#% global _debugsource_packages 0

%global Werror_cflags %nil
#define _disable_lto %nil
# enable in next version
%bcond_without python

%define api %{version}
%define libname	%mklibname %{name}
%define devname	%mklibname -d %{name}

Name:           uhd
URL:            https://github.com/EttusResearch/uhd
Version:	4.6.0.0
Release:	3
Summary:        Universal Hardware Driver for Ettus Research products
License:        GPLv3+
Source0:	https://github.com/EttusResearch/uhd/archive/v%{version}/%{name}-%{version}.tar.gz
Source100:      uhd.rpmlintrc

BuildRequires:  cmake
BuildRequires:  boost-devel
BuildRequires:  icu-devel
BuildRequires:	atomic-devel
BuildRequires:  boost-chrono-devel
BuildRequires:  boost-static-devel
BuildRequires:  pkgconfig(libusb-1.0)
BuildRequires:  pkgconfig(udev)
BuildRequires:  doxygen
BuildRequires:	python-mako
BuildRequires:	python-docutils
%if %{with python}
BuildRequires:	pkgconfig(python3)
BuildRequires:	python%{pyver}dist(mako)
BuildRequires:	python%{pyver}dist(requests)
BuildRequires:	python%{pyver}dist(numpy)
%endif

Requires:	%{libname} = %{EVRD}

%description
The UHD is the universal hardware driver for Ettus Research products.
The goal of the UHD is to provide a host driver and API for current and
future Ettus Research products. It can be used standalone without GNU Radio.

%prep
%autosetup -p1 -n %{name}-%{version}

%build
export GITREV=%{version}
%set_build_flags
cd host
mkdir build
pushd build
cmake .. -DENABLE_UTILS=ON \
	-DENABLE_E100=ON \
	-DENABLE_E300=ON \
	-DENABLE_PYTHON3=ON \
	-DENABLE_TESTS=OFF \
	-DUHD_VERSION=%{version} \
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

#find %{buildroot} -name "*.py" -print -exec 2to3 -w {} \;

%package doc
Summary:        Documentation files for UHD
Group:          Communications
BuildArch:      noarch

%package -n	%{libname}
Summary:	Universal Hardware Driver (UHD)
Group:		System/Libraries

%description -n	%{libname}
Universal Hardware Driver (UHD)

%package -n	%{devname}
Summary:	Development files for %{name}
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}
Provides:	%{name}-devel = %{version}-%{release}
Obsoletes:	%{name}-devel-doc < 1.0.15-2

%description -n	%{devname}
Development files for the Universal Hardware Driver (UHD).

%description doc
Documentation for the Universal Hardware Driver (UHD).

%if %{with python}
%package -n python-%{name}
Summary:	Python 3 bindings for %{uhd}
Group:		Development/Python
Requires:	%{name} = %{EVRD}

%description -n python-%{name}
python bindings for %{name}
%endif

%pre -n uhd
getent group usrp >/dev/null || groupadd -r usrp

%files
%{_bindir}/*
%{_mandir}/man1/%{name}*.*
%{_mandir}/man1/usrp*.*
%config(noreplace) %{_sysconfdir}/udev/rules.d/10-usrp-uhd.rules
%{_libexecdir}/uhd

%files -n %{libname}
%{_libdir}/lib*.so.*

%files -n %{devname}
%{_includedir}/*
%{_libdir}/lib*.so
%{_libdir}/pkgconfig/*.pc
%{_libdir}/cmake/uhd/UHDConfig.cmake
%{_libdir}/cmake/uhd/UHDConfigVersion.cmake
%{_libdir}/cmake/uhd/UHDBoost.cmake

%files doc
%{_datadir}/doc/uhd/LICENSE
%{_datadir}/doc/uhd/README.md
%{_docdir}/%{name}/doxygen/*/*
%{_datadir}/%{name}/

%if %{with python}
%files -n python-%{name}
%{python3_sitearch}/%{name}/
%{python3_sitearch}/usrp_mpm/
%endif

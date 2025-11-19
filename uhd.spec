#%% global debug_package %%{nil}
#%% global _debugsource_packages 0

%global Werror_cflags %nil
#define _disable_lto %%nil
# enable in next version
%bcond_without python

# By default include binary_firmware, otherwise try to rebuild
# the firmware from sources. If you want to rebuild all firmware
# images you need to install appropriate tools (e.g. Xilinx ISE).
%bcond_without binary_firmware

%define api %{version}
%define libname	%mklibname %{name}
%define devname	%mklibname -d %{name}

Name:		uhd
URL:		https://github.com/EttusResearch/uhd
Version:	4.9.0.1
#%%global images_ver %%{version}
%global images_ver 4.9.0.0
Release:	1
Summary:	Universal Hardware Driver for Ettus Research products
License:	GPL-3.0-or-later
Source0:	%{url}/archive/v%{version}/%{name}-%{version}.tar.gz
# uhd firmware
Source2:	%{url}/releases/download/v%{images_ver}/uhd-images_%{images_ver}.tar.xz
Source100:	uhd.rpmlintrc

BuildRequires:  cmake
# Since v 4.9.0.1 upstream added support for boost 1.89.0 and
# dropped support for boost lower than 1.71.0
BuildRequires:	boost-devel >= 1.71.0
BuildRequires:	icu-devel
BuildRequires:	atomic-devel
BuildRequires:	boost-chrono-devel
BuildRequires:	boost-static-devel
BuildRequires:	pkgconfig(libgps)
BuildRequires:	pkgconfig(libpcap)
BuildRequires:	pkgconfig(libusb-1.0)
BuildRequires:	pkgconfig(orc-0.4)
BuildRequires:	pkgconfig(udev)
BuildRequires:	doxygen
BuildRequires:	python-mako
BuildRequires:	python-docutils
BuildRequires:	sdcc
BuildRequires:	sed
%if %{with python}
BuildRequires:	pkgconfig(python3)
BuildRequires:	python%{pyver}dist(mako)
BuildRequires:	python%{pyver}dist(requests)
BuildRequires:	python%{pyver}dist(numpy)
BuildRequires:	python%{pyver}dist(setuptools)
%endif

Requires:	%{libname} = %{EVRD}

%description
The UHD is the universal hardware driver for Ettus Research products.
The goal of the UHD is to provide a host driver and API for current and
future Ettus Research products. It can be used standalone without GNU Radio.

%prep
%autosetup -p1 -n %{name}-%{version}

# firmware
%if %{with binary_firmware}
# extract binary firmware
mkdir -p images/images
tar -xJf %{SOURCE2} -C images/images --strip-components=1
rm -f images/images/{LICENSE.txt,*.tag}
# remove Windows drivers
rm -rf images/winusb_driver
%endif

# fix python shebangs
find . -type f -name "*.py" -exec sed -i '/^#!/ s|.*|#!%{__python3}|' {} \;

# Create a sysusers.d config file
cat >uhd.sysusers.conf <<EOF
g usrp -
EOF


%build
# firmware
%if ! %{with binary_firmware}
# rebuilt from sources
export PATH=$PATH:%{_libexecdir}/sdcc
pushd images
sed -i '/-name "\*\.twr" | xargs grep constraint | grep met/ s/^/#/' Makefile
make %{?_smp_mflags} images
popd
%endif
# NOTE switch to GCC to compile, there is an issue compiling UHD with clang 21
# NOTE related upstream issue https://github.com/EttusResearch/uhd/issues/881
export CC=/usr/bin/gcc
export CXX=/usr/bin/g++
export CXXFLAGS="%{optflags}"
export LDFLAGS="-Wl,--as-needed"
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
	-DPYTHON_EXECUTABLE:FILEPATH=%{__python} \
	-DCMAKE_INSTALL_PREFIX:PATH=%{_prefix} \
	-DCMAKE_INSTALL_LIBDIR:PATH=%{_lib} \
	-DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
	-G Ninja

%ninja_build
popd

%check
pushd host
%ninja_build test -C build

%install
pushd host
%ninja_install -C build

# Allow access only to users in usrp group
sed -i 's/MODE:="0666"/MODE:="0660"/' %{buildroot}%{_libdir}/uhd/utils/uhd-usrp.rules
mkdir -p %{buildroot}%{_sysconfdir}/udev/rules.d
mv %{buildroot}%{_libdir}/uhd/utils/uhd-usrp.rules %{buildroot}%{_sysconfdir}/udev/rules.d/10-usrp-uhd.rules

# Remove tests, examples binaries
rm -rf %{buildroot}%{_libdir}/uhd/{tests,examples}

# Move the utils stuff to libexec dir
mkdir -p %{buildroot}%{_libexecdir}/uhd
mv %{buildroot}%{_libdir}/uhd/utils/* %{buildroot}%{_libexecdir}/uhd
popd

# firmware
mkdir -p %{buildroot}%{_datadir}/uhd/images
cp -r images/images/* %{buildroot}%{_datadir}/uhd/images

#find %{buildroot} -name "*.py" -print -exec 2to3 -w {} \;

%package doc
Summary:        Documentation files for UHD
Group:          Communications
BuildArch:      noarch

%description doc
Documentation for the Universal Hardware Driver (UHD).

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


%package firmware
Summary:        Firmware files for UHD
Requires:       %{name} = %{version}-%{release}
BuildArch:      noarch

%description firmware
Firmware files for the Universal Hardware driver (UHD).

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
%{_mandir}/man1/*.1*
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
%{_libdir}/cmake/uhd/UHDMinDepVersions.cmake
%{_libdir}/cmake/uhd/UHDPython.cmake
%{_libdir}/cmake/uhd/UHDUnitTest.cmake

%files firmware
%dir %{_datadir}/uhd/images
%{_datadir}/uhd/images/*

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

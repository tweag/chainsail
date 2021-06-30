import Link from 'next/link';
import { useRouter } from 'next/router';
import firebase from 'firebase/app';
import nookies from 'nookies';

import { FlexCenter, FlexRow, FlexCol } from './Flex';
import Container from './Container';
import { useAuth } from './Auth';
import { useState } from 'react';

const NavItem = (props) => {
  const style = `px-6 py-1 rounded-md hover:bg-gray-800 transition duration-300 cursor-pointer ${props.className}`;
  if (props.internal) {
    return (
      <Link href={props.href}>
        <a className={style}>{props.children}</a>
      </Link>
    );
  }
  if (props.href) {
    return (
      <a className={style} href={props.href}>
        {props.children}
      </a>
    );
  }
  if (props.onClick) {
    return (
      <a className={style} onClick={props.onClick}>
        {props.children}
      </a>
    );
  }
};

const logout = async () => {
  await firebase.auth().signOut();
  window.location.href = '/';
};

const LogInLogOut = ({ user, providerData, route }) => {
  const styleLogInOut = 'border-gray-100 border-2 hover:border-opacity-0 border-opacity-20';
  return (
    <div className="mt-5 ml-6 md:mt-0 md:ml-0">
      {!user && (
        <NavItem
          className={styleLogInOut}
          onClick={() => {
            nookies.set(undefined, 'latestPage', route, {});
            window.location = '/login';
          }}
        >
          Login
        </NavItem>
      )}
      {user && (
        <FlexRow className="items-center space-x-2">
          {providerData && (
            <FlexCenter>
              <img
                width="35"
                height="35"
                src={providerData[0].photoURL}
                className="rounded-full"
              />
            </FlexCenter>
          )}
          <NavItem onClick={logout} className={styleLogInOut}>
            Logout
          </NavItem>
        </FlexRow>
      )}
    </div>
  );
};

const MobileNavbar = ({ user, providerData, route, navActive, setNavActive }) => {
  return (
    <div className="relative">
      <FlexCenter
        className="w-10 h-10 m-6 border-2 rounded-full"
        onClick={() => setNavActive((s) => !s)}
      >
        <i className="fas fa-bars"></i>
      </FlexCenter>
      <FlexCol
        className={`fixed top-0 left-0 z-10 h-screen bg-gray-900 w-screen transition duration-500 ${
          navActive ? 'opacity-100' : 'hidden opacity-0'
        }`}
      >
        <FlexCenter
          className="w-10 h-10 m-6 border-2 rounded-full"
          onClick={() => {
            window.scrollTo(0, 0);
            setNavActive((s) => !s);
          }}
        >
          <i className="fas fa-arrow-left"></i>
        </FlexCenter>
        <NavItem internal href="/">
          Home
        </NavItem>
        <NavItem internal href="/job">
          Create new job
        </NavItem>
        <NavItem internal href="/results">
          My jobs
        </NavItem>
        <LogInLogOut user={user} providerData={providerData} route={route} />
      </FlexCol>
    </div>
  );
};

const BigScreensNavbar = ({ user, providerData, route }) => {
  return (
    <Container>
      <FlexRow between className="items-center h-16 text-sm text-white md:text-base">
        <FlexRow className="items-center space-x-2">
          <NavItem internal href="/">
            Home
          </NavItem>
          <NavItem internal href="/job">
            Create new job
          </NavItem>
          <NavItem internal href="/results">
            My jobs
          </NavItem>
        </FlexRow>
        <LogInLogOut user={user} providerData={providerData} route={route} />
      </FlexRow>
    </Container>
  );
};

const Navbar = ({ isMobile }) => {
  const { user } = useAuth();
  const providerData = user ? user.providerData : undefined;
  const { route } = useRouter();
  const [navActive, setNavActive] = useState(false);
  if (isMobile) {
    return (
      <MobileNavbar
        user={user}
        providerData={providerData}
        route={route}
        navActive={navActive}
        setNavActive={setNavActive}
      />
    );
  } else {
    return <BigScreensNavbar user={user} providerData={providerData} route={route} />;
  }
};
export default Navbar;

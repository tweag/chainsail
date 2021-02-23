import Link from 'next/link';
import Image from 'next/image';
import firebase from 'firebase/app';

import { FlexCenter, FlexRow } from './Flex';
import { useAuth } from './Auth';

const NavItem = (props) => {
  const style = `px-6 py-1 border-white border-opacity-20 hover:opacity-60 transition duration-300 cursor-pointer ${props.className}`;
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

const Navbar = () => {
  const { user } = useAuth();
  const providerData = user ? user.providerData : undefined;
  const styleLogInOut = 'border-white rounded-md border-2';
  return (
    <FlexRow between className="items-center h-16 text-sm md:text-base">
      <FlexRow className="space-x-2 items-end">
        <NavItem internal href="/">
          Home
        </NavItem>
        <NavItem internal href="/job">
          Create a new job!
        </NavItem>
        <NavItem internal href="/job/results">
          latest jobs
        </NavItem>
      </FlexRow>
      <div>
        {!user && (
          <NavItem internal href="/login" className={styleLogInOut}>
            Login
          </NavItem>
        )}
        {user && (
          <FlexRow className="items-end space-x-2">
            {providerData && (
              <FlexCenter>
                <Image
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
    </FlexRow>
  );
};
export default Navbar;

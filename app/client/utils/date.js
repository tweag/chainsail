import moment from 'moment';

export const dateFormatter = (d) => {
  if (d) return moment(d).format('DD MMM hh:mm');
  else return '---';
};

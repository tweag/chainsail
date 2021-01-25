import { useState } from 'react';
import {
  Container,
  Link,
  Layout,
  FlexRow,
  FlexCol,
  FlexCenter,
  FormField,
  Math,
  Navbar,
  Modal,
} from '../../components';

const FieldDescription = ({ children, name, activeField, icon, math }) => (
  <div
    className={`${
      activeField === name ? 'text-blue-400' : ''
    } transition duration-200 my-1 lg:my-0`}
  >
    {icon && <i className={`${icon} mr-5`}></i>}
    {math && (
      <Math inline className="mr-5">
        {math}
      </Math>
    )}
    {children}
  </div>
);

const Descs = ({ activeField }) => {
  return (
    <FlexCol between className="w-full h-full">
      <FieldDescription activeField={activeField} name="job_name" icon="fas fa-bars">
        Job name: a unique key id for your job.
      </FieldDescription>
      <FieldDescription activeField={activeField} name="max_replicas" icon="fas fa-cloud">
        Max N° replicas: maximum number of replicas to use. Specifics of the environment in which
        these are created is configured on the scheduler itself
      </FieldDescription>
      <FieldDescription
        activeField={activeField}
        name="tempered_distribution_family"
        math="\{\mathbb{P}\}"
      >
        Tempered distribution family: the family of tempered distributions to use. For now, the only
        valid value is "Boltzmann"
      </FieldDescription>
      <FieldDescription activeField={activeField} name="minimum_beta" math="\beta_{min}">
        Beta min: the minimum inverse temperature (beta) which determines the flatness of the
        flattest distribution
      </FieldDescription>
      <FieldDescription activeField={activeField} name="initial_schedule_beta_ratio" math="\alpha">
        Initial schedule beta ratio: the ratio defining (approximately) the geometric progression
      </FieldDescription>
      <FieldDescription activeField={activeField} name="probability_definition" icon="fas fa-link">
        Probability definition: URL to archive including importable Python module providing the log
        probability
      </FieldDescription>
      <FieldDescription activeField={activeField} name="dependencies" icon="fas fa-bolt">
        Dependencies: list of dependencies to install on compute nodes
      </FieldDescription>
    </FlexCol>
  );
};

const JobPageModal = ({ jobCreated, jobId, err, errMsg, setErr, setErrMsg }) => {
  return (
    <Modal isActive={jobCreated || err}>
      {!err && (
        <>
          <div className="mb-7">
            Job with id {jobId} created successfully. Please look at result page to check its latest
            status.
          </div>
          <FlexCenter>
            <Link href="/job/results">
              <a
                className={
                  'px-6 py-2 text-base text-center bg-purple-700  ' +
                  ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
                }
              >
                Checkout results!
              </a>
            </Link>
          </FlexCenter>
        </>
      )}
      {err && (
        <>
          <div className="mb-7">{errMsg.message}</div>
          <FlexCenter>
            <a
              className={
                'px-6 py-2 text-base text-center bg-purple-700  ' +
                ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
              }
              onClick={() => {
                setErr(false);
                setErrMsg('');
              }}
            >
              Try again!
            </a>
          </FlexCenter>
        </>
      )}
    </Modal>
  );
};

export default function Job() {
  const [activeField, setActiveField] = useState('other');
  const [jobCreated, setJobCreated] = useState(false);

  // Form fields state variables
  const [job_name, setJobName] = useState('');
  const [max_replicas, setMaxReplicas] = useState(1);
  const [initial_number_of_replicas, setInitNReplicas] = useState(1);
  const [tempered_distribution_family, setTemperedDist] = useState('boltzmann');
  const [minimum_beta, setMinBeta] = useState(0.01);
  const [initial_schedule_beta_ratio, setInitScheduleBetaRatio] = useState(1);
  const [probability_definition, setProbDef] = useState('');
  const [dependencies, setDeps] = useState([]);

  const [createdJobId, setCreatedJobID] = useState(null);

  // Error handling states
  const [err, setErr] = useState(false);
  const [errMsg, setErrMsg] = useState('');

  const createJob = async () => {
    const FLASK_URL = process.env.FLASK_URL || 'http://127.0.0.1:5000';
    const JOB_CREATION_ENDPOINT = '/job';
    const body = JSON.stringify({
      //TODO: should be checked in scheduler job schema whether job_name is required
      initial_number_of_replicas,
      max_replicas,
      tempered_dist_family: tempered_distribution_family,
      initial_schedule_parameters: {
        minimum_beta,
        beta_ratio: initial_schedule_beta_ratio,
      },
      probability_definition,
      dependencies: [{ type: 'pip', deps: dependencies }],
    });

    const requestOptions = {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    };
    try {
      let response = await fetch(`${FLASK_URL}${JOB_CREATION_ENDPOINT}`, requestOptions);
      let data = await response.json();
      if (response.status === 200) {
        setJobCreated(true);
        if (data.job_id) setCreatedJobID(data.job_id);
      }
    } catch (e) {
      setErr(true);
      setErrMsg(e);
    }
  };

  return (
    <Layout>
      <JobPageModal
        jobCreated={jobCreated}
        jobId={createdJobId}
        err={err}
        errMsg={errMsg}
        setErr={setErr}
        setErrMsg={setErrMsg}
      />
      <Container className="text-white bg-gradient-to-r from-purple-900 to-indigo-600 lg:h-screen font-body">
        <FlexCol between className="h-full">
          <Navbar />
          <FlexCenter className="w-full h-full py-5 md:py-20">
            <FlexCol center className="w-full h-full">
              <div className="mb-10 text-2xl md:text-5xl lg:text-6xl">
                Run a sampling task
                <i className="ml-3 fas fa-rocket"></i>
              </div>
              <div className="w-full mb-20 text-base md:text-xl lg:w-2/3 md:text-justify">
                Every sampling task is called a <em>job</em>. Every job is specified through several
                attributes. After a job is submitted, the user gets a link to a cloud bucket, which
                contains the samples, sampling statistics such as acceptance rates and an estimate
                of the density of states.
              </div>
              <FlexRow
                between
                responsive
                media="lg"
                className="w-full lg:px-20 lg:h-3/5 lg:space-x-20"
              >
                <FlexCenter className="flex-grow mb-10 lg:py-10 h-96 md:h-80 lg:h-full lg:mb-0">
                  <form
                    className="w-full h-full"
                    onSubmit={(e) => {
                      e.preventDefault();
                      createJob(e);
                    }}
                  >
                    <FlexCol between className="w-full h-full">
                      <FormField
                        label="Job name"
                        inputName="job_name"
                        setActiveField={setActiveField}
                        value={job_name}
                        onChange={(e) => setJobName(e.target.value)}
                      />
                      <FlexRow
                        responsive
                        media="md"
                        className="space-y-1 md:space-y-0 md:space-x-5"
                      >
                        <FormField
                          label="Initial N° replicas"
                          inputName="initial_number_of_replicas"
                          setActiveField={setActiveField}
                          value={initial_number_of_replicas}
                          onChange={(e) => setInitNReplicas(e.target.value)}
                        />
                        <FormField
                          label="Max N° replicas"
                          inputName="max_replicas"
                          inputType="number"
                          setActiveField={setActiveField}
                          minNumber={1}
                          value={max_replicas}
                          onChange={(e) => setMaxReplicas(e.target.value)}
                        />
                      </FlexRow>
                      <FormField
                        label="Tempered distribution family"
                        inputName="tempered_distribution_family"
                        hasDropdown
                        setActiveField={setActiveField}
                        disabled
                        defaultValue="Boltzmann"
                        value={tempered_distribution_family}
                        onChange={(e) => setTemperedDist(e.target.value)}
                      />
                      <FlexRow
                        responsive
                        media="md"
                        className="space-y-1 md:space-y-0 md:space-x-5"
                      >
                        <FormField
                          label="Beta min"
                          inputName="minimum_beta"
                          inputType="number"
                          setActiveField={setActiveField}
                          minNumber={0}
                          maxNumber={1}
                          stepNumber={0.01}
                          value={minimum_beta}
                          onChange={(e) => setMinBeta(e.target.value)}
                        />
                        <FormField
                          label="Initial schedule beta ratio"
                          inputName="initial_schedule_beta_ratio"
                          inputType="text"
                          setActiveField={setActiveField}
                          value={initial_schedule_beta_ratio}
                          onChange={(e) => setInitScheduleBetaRatio(e.target.value)}
                        />
                      </FlexRow>
                      <FormField
                        label="Probability definition"
                        inputName="probability_definition"
                        inputType="url"
                        setActiveField={setActiveField}
                        value={probability_definition}
                        onChange={(e) => setProbDef(e.target.value)}
                      />
                      <FormField
                        label="Dependencies"
                        inputName="dependencies"
                        inputType="text"
                        setActiveField={setActiveField}
                        value={dependencies}
                        onChange={(e) => setDeps(e.target.value.split(','))}
                        className="mb-5"
                      />

                      <FlexCenter>
                        <input
                          type="submit"
                          value="Submit"
                          className={
                            'w-52 px-6 pt-3 pb-4 text-base text-center bg-purple-700  ' +
                            ' rounded-lg cursor-pointer lg:transition lg:duration-300 hover:bg-purple-900 text-white'
                          }
                        />
                      </FlexCenter>
                    </FlexCol>
                  </form>
                </FlexCenter>
                <FlexCenter className="w-full p-5 bg-gray-700 md:p-10 lg:w-1/2 lg:h-full rounded-xl">
                  <Descs activeField={activeField} />
                </FlexCenter>
              </FlexRow>
            </FlexCol>
          </FlexCenter>
        </FlexCol>
      </Container>
    </Layout>
  );
}
